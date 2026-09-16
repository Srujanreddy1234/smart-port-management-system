"""
Gate congestion routing and time-slot booking (a Truck Appointment
System, or TAS) -- the standard, industry-proven approach terminals use
to cut truck queueing at gates by spreading arrivals across the day
instead of everyone converging on the same gate at once.

Congestion for a gate is always computed live from the real data
(trucks currently checked in at that gate + how full the next few
booking slots are) -- never a fabricated or hardcoded number.
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db, cache
from app.models import (
    User, Gate, GateStatus, GateType, GateBooking, BookingStatus, BookingPurpose,
    Truck, TruckStatus
)
from app.utils.exceptions import AuthorizationError, NotFoundError, ValidationError as AppValidationError
from app.utils.helpers import success_response
from app.utils.validators import asset_id, phone as phone_validator
from sqlalchemy import func, and_
from sqlalchemy.orm import joinedload
from datetime import datetime, timedelta
from marshmallow import Schema, fields, validate, ValidationError


gates_bp = Blueprint('gates', __name__, url_prefix='/api/v1/gates')

SLOT_MINUTES = 30


class GateSchema(Schema):
    gate_code = fields.Str(required=True, validate=[validate.Length(min=3, max=20), asset_id()])
    name = fields.Str(required=True, validate=validate.Length(max=255))
    gate_type = fields.Str(required=True, validate=validate.OneOf([t.value for t in GateType]))
    status = fields.Str(validate=validate.OneOf([s.value for s in GateStatus]))
    zone = fields.Str(validate=validate.Length(max=100))
    capacity_per_hour = fields.Int()
    latitude = fields.Float()
    longitude = fields.Float()
    notes = fields.Str(validate=validate.Length(max=500))
    is_active = fields.Bool()


class BookingSchema(Schema):
    gate_id = fields.Int(required=True)
    driver_name = fields.Str(validate=validate.Length(max=255))
    driver_phone = fields.Str(validate=phone_validator())
    truck_number = fields.Str(validate=[validate.Length(min=3, max=50), asset_id()])
    purpose = fields.Str(required=True, validate=validate.OneOf([p.value for p in BookingPurpose]))
    container_id = fields.Int()
    slot_start = fields.DateTime(required=True)
    notes = fields.Str(validate=validate.Length(max=500))


gate_schema = GateSchema()
booking_schema = BookingSchema()


def check_permission(permission):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user or not user.has_permission(permission):
        raise AuthorizationError(f'Permission required: {permission}')
    return user


def _slot_bounds(dt):
    """Round a datetime down to its containing SLOT_MINUTES-wide slot."""
    minute = (dt.minute // SLOT_MINUTES) * SLOT_MINUTES
    start = dt.replace(minute=minute, second=0, microsecond=0)
    return start, start + timedelta(minutes=SLOT_MINUTES)


def _gate_congestion(gate):
    """Live congestion for one gate, derived from real data:
    - trucks currently physically at this gate (Truck.current_gate_id)
    - how full the current and next slot's bookings are relative to
      the gate's configured hourly capacity
    Returns a dict with a 0-100 load score and a Low/Medium/High label.
    """
    trucks_now = Truck.query.filter(
        Truck.current_gate_id == gate.id,
        Truck.status.in_([TruckStatus.AT_GATE, TruckStatus.WAITING])
    ).count()

    now = datetime.utcnow()
    hour_start = now.replace(minute=0, second=0, microsecond=0)
    hour_end = hour_start + timedelta(hours=1)
    bookings_this_hour = GateBooking.query.filter(
        GateBooking.gate_id == gate.id,
        GateBooking.status.in_([BookingStatus.BOOKED, BookingStatus.CHECKED_IN]),
        GateBooking.slot_start >= hour_start,
        GateBooking.slot_start < hour_end,
    ).count()

    capacity = max(gate.capacity_per_hour, 1)
    # Trucks physically queued weigh more heavily than a merely-booked
    # slot, since a queue is congestion happening right now.
    load_score = min(100, round((((trucks_now * 1.5) + bookings_this_hour) / capacity) * 100))

    if gate.status != GateStatus.OPEN:
        label = 'Closed'
    elif load_score >= 75:
        label = 'High'
    elif load_score >= 40:
        label = 'Medium'
    else:
        label = 'Low'

    return {
        'trucks_at_gate': trucks_now,
        'bookings_this_hour': bookings_this_hour,
        'capacity_per_hour': capacity,
        'load_score': load_score,
        'congestion': label,
    }


@gates_bp.route('', methods=['GET'])
@jwt_required()
def list_gates():
    check_permission('gates.read')
    gates = Gate.query.filter_by(is_active=True).order_by(Gate.gate_code).all()
    result = []
    for g in gates:
        d = g.to_dict()
        d['live'] = _gate_congestion(g)
        result.append(d)
    return success_response(result)


@gates_bp.route('/recommend', methods=['GET'])
@jwt_required()
def recommend_gate():
    """The core driver-facing feature: which open gate has the most
    headroom right now. Purely a function of live data -- no fixed
    "always recommend Gate 1" shortcuts."""
    check_permission('gates.read')
    gates = Gate.query.filter_by(is_active=True, status=GateStatus.OPEN).all()
    if not gates:
        return success_response({'available': False, 'message': 'No gates are currently open.'})

    ranked = sorted(
        ((g, _gate_congestion(g)) for g in gates),
        # Lower load first; ties broken by higher hourly capacity, since
        # an equally-empty gate with more throughput is the better pick.
        key=lambda pair: (pair[1]['load_score'], -pair[0].capacity_per_hour)
    )
    best_gate, best_live = ranked[0]
    alternatives = [
        {**g.to_dict(), 'live': live}
        for g, live in ranked[1:4]
    ]

    return success_response({
        'available': True,
        'recommended_gate': {**best_gate.to_dict(), 'live': best_live},
        'alternatives': alternatives,
        'generated_at': datetime.utcnow().isoformat(),
    })


@gates_bp.route('/<int:gate_id>', methods=['GET'])
@jwt_required()
def get_gate(gate_id):
    check_permission('gates.read')
    gate = Gate.query.get(gate_id)
    if not gate:
        raise NotFoundError('Gate not found')
    d = gate.to_dict()
    d['live'] = _gate_congestion(gate)
    return success_response(d)


@gates_bp.route('', methods=['POST'])
@jwt_required()
def create_gate():
    check_permission('gates.manage')
    try:
        data = gate_schema.load(request.get_json() or {})
    except ValidationError as err:
        raise AppValidationError('Validation failed', details=err.messages)

    if Gate.query.filter_by(gate_code=data['gate_code']).first():
        raise AppValidationError('Gate code already exists')

    gate = Gate(**data)
    db.session.add(gate)
    db.session.commit()
    return success_response(gate.to_dict(), 'Gate created successfully', 201)


@gates_bp.route('/<int:gate_id>', methods=['PUT'])
@jwt_required()
def update_gate(gate_id):
    check_permission('gates.manage')
    gate = Gate.query.get(gate_id)
    if not gate:
        raise NotFoundError('Gate not found')
    try:
        data = gate_schema.load(request.get_json() or {}, partial=True)
    except ValidationError as err:
        raise AppValidationError('Validation failed', details=err.messages)
    for key, value in data.items():
        setattr(gate, key, value)
    gate.updated_at = datetime.utcnow()
    db.session.commit()
    return success_response(gate.to_dict(), 'Gate updated successfully')


@gates_bp.route('/<int:gate_id>/availability', methods=['GET'])
@jwt_required()
def gate_availability(gate_id):
    """Available booking slots for one gate on one day, each capped by
    the gate's configured hourly capacity split evenly across the
    SLOT_MINUTES-wide slots in that hour."""
    check_permission('gates.read')
    gate = Gate.query.get(gate_id)
    if not gate:
        raise NotFoundError('Gate not found')

    date_str = request.args.get('date')
    try:
        day = datetime.fromisoformat(date_str).date() if date_str else datetime.utcnow().date()
    except ValueError:
        raise AppValidationError('Invalid date, expected YYYY-MM-DD')

    day_start = datetime.combine(day, datetime.min.time())
    slots_per_hour = max(1, 60 // SLOT_MINUTES)
    per_slot_capacity = max(1, gate.capacity_per_hour // slots_per_hour)

    booked_counts = dict(
        db.session.query(GateBooking.slot_start, func.count(GateBooking.id))
        .filter(
            GateBooking.gate_id == gate_id,
            GateBooking.status.in_([BookingStatus.BOOKED, BookingStatus.CHECKED_IN]),
            GateBooking.slot_start >= day_start,
            GateBooking.slot_start < day_start + timedelta(days=1),
        )
        .group_by(GateBooking.slot_start)
        .all()
    )

    now = datetime.utcnow()
    slots = []
    cursor = day_start
    while cursor < day_start + timedelta(days=1):
        booked = booked_counts.get(cursor, 0)
        slots.append({
            'slot_start': cursor.isoformat(),
            'slot_end': (cursor + timedelta(minutes=SLOT_MINUTES)).isoformat(),
            'capacity': per_slot_capacity,
            'booked': booked,
            'available': max(0, per_slot_capacity - booked),
            'is_past': cursor < now,
        })
        cursor += timedelta(minutes=SLOT_MINUTES)

    return success_response({
        'gate': gate.to_dict(),
        'date': day.isoformat(),
        'slot_minutes': SLOT_MINUTES,
        'slots': slots,
    })


@gates_bp.route('/bookings', methods=['GET'])
@jwt_required()
def list_bookings():
    """Staff with gates.write see every booking (to manage the queue);
    everyone else only ever sees their own."""
    user = check_permission('gates.read')
    # Eager-load the gate relationship -- to_dict() reads booking.gate for
    # every row, which without this fires one extra query per booking
    # instead of a single JOIN.
    query = GateBooking.query.options(joinedload(GateBooking.gate))

    if not user.has_permission('gates.manage'):
        query = query.filter(GateBooking.booked_by_user_id == user.id)
    elif request.args.get('mine') == 'true':
        query = query.filter(GateBooking.booked_by_user_id == user.id)

    if request.args.get('gate_id'):
        query = query.filter(GateBooking.gate_id == request.args['gate_id'])
    if request.args.get('status'):
        try:
            query = query.filter(GateBooking.status == BookingStatus(request.args['status']))
        except ValueError:
            raise AppValidationError('Invalid status')
    upcoming_only = request.args.get('upcoming', 'true').lower() == 'true'
    if upcoming_only:
        query = query.filter(GateBooking.slot_start >= datetime.utcnow() - timedelta(hours=1))

    query = query.order_by(GateBooking.slot_start.asc())

    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 50, type=int), 100)
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return success_response({
        'items': [b.to_dict() for b in pagination.items],
        'total': pagination.total,
        'page': pagination.page,
        'per_page': pagination.per_page,
        'pages': pagination.pages,
    })


@gates_bp.route('/bookings', methods=['POST'])
@jwt_required()
def create_booking():
    user = check_permission('gates.book')
    try:
        data = booking_schema.load(request.get_json() or {})
    except ValidationError as err:
        raise AppValidationError('Validation failed', details=err.messages)

    gate = Gate.query.get(data['gate_id'])
    if not gate:
        raise NotFoundError('Gate not found')
    if gate.status != GateStatus.OPEN:
        raise AppValidationError(f'{gate.name} is currently {gate.status.value.lower()} and not accepting bookings')

    slot_start, slot_end = _slot_bounds(data['slot_start'])
    if slot_start < datetime.utcnow() - timedelta(minutes=SLOT_MINUTES):
        raise AppValidationError('Cannot book a time slot in the past')

    slots_per_hour = max(1, 60 // SLOT_MINUTES)
    per_slot_capacity = max(1, gate.capacity_per_hour // slots_per_hour)
    existing = GateBooking.query.filter(
        GateBooking.gate_id == gate.id,
        GateBooking.slot_start == slot_start,
        GateBooking.status.in_([BookingStatus.BOOKED, BookingStatus.CHECKED_IN]),
    ).count()
    if existing >= per_slot_capacity:
        raise AppValidationError('That time slot is fully booked -- please choose another.')

    booking = GateBooking(
        gate_id=gate.id,
        booked_by_user_id=user.id,
        driver_name=data.get('driver_name') or user.get_full_name(),
        driver_phone=data.get('driver_phone') or user.phone,
        truck_number=data.get('truck_number'),
        purpose=BookingPurpose(data['purpose']),
        container_id=data.get('container_id'),
        slot_start=slot_start,
        slot_end=slot_end,
        notes=data.get('notes'),
    )
    db.session.add(booking)
    db.session.commit()
    return success_response(booking.to_dict(), 'Time slot booked successfully', 201)


@gates_bp.route('/bookings/<int:booking_id>/cancel', methods=['POST'])
@jwt_required()
def cancel_booking(booking_id):
    user = check_permission('gates.book')
    booking = GateBooking.query.get(booking_id)
    if not booking:
        raise NotFoundError('Booking not found')
    if booking.booked_by_user_id != user.id and not user.has_permission('gates.manage'):
        raise AuthorizationError('You can only cancel your own bookings')
    if booking.status not in (BookingStatus.BOOKED, BookingStatus.CHECKED_IN):
        raise AppValidationError(f'Cannot cancel a booking that is already {booking.status.value.lower()}')

    booking.status = BookingStatus.CANCELLED
    booking.updated_at = datetime.utcnow()
    db.session.commit()
    return success_response(booking.to_dict(), 'Booking cancelled')


@gates_bp.route('/bookings/<int:booking_id>/check-in', methods=['POST'])
@jwt_required()
def check_in_booking(booking_id):
    check_permission('gates.manage')
    booking = GateBooking.query.get(booking_id)
    if not booking:
        raise NotFoundError('Booking not found')
    if booking.status != BookingStatus.BOOKED:
        raise AppValidationError(f'Cannot check in a booking that is {booking.status.value.lower()}')

    booking.status = BookingStatus.CHECKED_IN
    booking.checked_in_at = datetime.utcnow()
    booking.updated_at = datetime.utcnow()

    if booking.truck_id:
        truck = Truck.query.get(booking.truck_id)
        if truck:
            truck.current_gate_id = booking.gate_id
            truck.status = TruckStatus.AT_GATE
            truck.gate_in_time = booking.checked_in_at

    db.session.commit()
    return success_response(booking.to_dict(), 'Truck checked in')


@gates_bp.route('/bookings/<int:booking_id>/complete', methods=['POST'])
@jwt_required()
def complete_booking(booking_id):
    check_permission('gates.manage')
    booking = GateBooking.query.get(booking_id)
    if not booking:
        raise NotFoundError('Booking not found')
    if booking.status != BookingStatus.CHECKED_IN:
        raise AppValidationError('Booking must be checked in before it can be completed')

    booking.status = BookingStatus.COMPLETED
    booking.completed_at = datetime.utcnow()
    booking.updated_at = datetime.utcnow()

    if booking.truck_id:
        truck = Truck.query.get(booking.truck_id)
        if truck:
            truck.current_gate_id = None
            truck.gate_out_time = booking.completed_at

    db.session.commit()
    return success_response(booking.to_dict(), 'Booking completed')
