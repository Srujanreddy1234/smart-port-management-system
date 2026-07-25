from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from marshmallow import Schema, fields, validate, ValidationError
from app.extensions import db
from app.models import Ship, ShipStatus, VesselType, User
from app.utils.exceptions import ValidationError as AppValidationError, NotFoundError, AuthorizationError
from app.utils.helpers import success_response, paginate_query, apply_filters
from sqlalchemy import func, or_, desc, asc
from datetime import datetime


ships_bp = Blueprint('ships', __name__, url_prefix='/api/v1/ships')


class ShipSchema(Schema):
    id = fields.Int(dump_only=True)
    ship_id = fields.Str(required=True, validate=validate.Length(max=50))
    name = fields.Str(required=True, validate=validate.Length(max=255))
    vessel_type = fields.Str(required=True, validate=validate.OneOf([v.value for v in VesselType]))
    flag = fields.Str(required=True, validate=validate.Length(max=100))
    imo_number = fields.Str(validate=validate.Length(max=20))
    mmsi = fields.Str(validate=validate.Length(max=20))
    call_sign = fields.Str(validate=validate.Length(max=20))
    length_overall = fields.Float()
    beam = fields.Float()
    draft = fields.Float()
    gross_tonnage = fields.Int()
    deadweight_tonnage = fields.Int()
    max_containers = fields.Int()
    status = fields.Str(validate=validate.OneOf([s.value for s in ShipStatus]))
    current_berth = fields.Str(validate=validate.Length(max=50))
    eta = fields.DateTime()
    etd = fields.DateTime()
    agent = fields.Str(validate=validate.Length(max=255))
    agent_contact = fields.Str(validate=validate.Length(max=255))
    agent_email = fields.Email()
    cargo_description = fields.Str()
    containers_onboard = fields.Int()
    containers_to_load = fields.Int()
    containers_to_discharge = fields.Int()


ship_schema = ShipSchema()
ship_list_schema = ShipSchema(many=True)


@ships_bp.route('', methods=['GET'])
@jwt_required()
def list_ships():
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)
    search = request.args.get('search', '').strip()
    status = request.args.get('status')
    vessel_type = request.args.get('vessel_type')
    berth = request.args.get('berth')
    sort_by = request.args.get('sort_by', 'created_at')
    sort_order = request.args.get('sort_order', 'desc')

    query = Ship.query

    if search:
        query = query.filter(or_(
            Ship.name.ilike(f'%{search}%'),
            Ship.ship_id.ilike(f'%{search}%'),
            Ship.agent.ilike(f'%{search}%'),
            Ship.imo_number.ilike(f'%{search}%')
        ))

    if status:
        try:
            query = query.filter(Ship.status == ShipStatus(status))
        except ValueError:
            raise AppValidationError(f'Invalid status: {status}')

    if vessel_type:
        try:
            query = query.filter(Ship.vessel_type == VesselType(vessel_type))
        except ValueError:
            raise AppValidationError(f'Invalid vessel type: {vessel_type}')

    if berth:
        query = query.filter(Ship.current_berth == berth)

    sort_column = getattr(Ship, sort_by, Ship.created_at)
    if sort_order == 'desc':
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(asc(sort_column))

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return success_response({
        'items': [ship.to_dict() for ship in pagination.items],
        'total': pagination.total,
        'page': pagination.page,
        'per_page': pagination.per_page,
        'pages': pagination.pages,
        'has_next': pagination.has_next,
        'has_prev': pagination.has_prev
    })


@ships_bp.route('/<int:ship_id>', methods=['GET'])
@jwt_required()
def get_ship(ship_id):
    ship = Ship.query.get(ship_id)
    if not ship:
        raise NotFoundError('Ship not found')
    return success_response(ship.to_dict())


@ships_bp.route('', methods=['POST'])
@jwt_required()
def create_ship():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if not user or not user.has_permission('ships.write'):
        raise AuthorizationError('Insufficient permissions')

    try:
        data = ship_schema.load(request.get_json() or {})
    except ValidationError as err:
        return jsonify({'success': False, 'errors': err.messages}), 400

    if Ship.query.filter_by(ship_id=data['ship_id']).first():
        raise AppValidationError('Ship ID already exists')

    if data.get('imo_number') and Ship.query.filter_by(imo_number=data['imo_number']).first():
        raise AppValidationError('IMO number already exists')

    ship = Ship(**data)
    db.session.add(ship)
    db.session.commit()

    return success_response(ship.to_dict(), 'Ship created successfully', 201)


@ships_bp.route('/<int:ship_id>', methods=['PUT'])
@jwt_required()
def update_ship(ship_id):
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if not user or not user.has_permission('ships.write'):
        raise AuthorizationError('Insufficient permissions')

    ship = Ship.query.get(ship_id)
    if not ship:
        raise NotFoundError('Ship not found')

    try:
        data = ship_schema.load(request.get_json() or {}, partial=True)
    except ValidationError as err:
        return jsonify({'success': False, 'errors': err.messages}), 400

    if 'ship_id' in data and data['ship_id'] != ship.ship_id:
        if Ship.query.filter_by(ship_id=data['ship_id']).first():
            raise AppValidationError('Ship ID already exists')
        ship.ship_id = data['ship_id']

    if 'imo_number' in data and data['imo_number'] != ship.imo_number:
        if data['imo_number'] and Ship.query.filter_by(imo_number=data['imo_number']).first():
            raise AppValidationError('IMO number already exists')
        ship.imo_number = data['imo_number']

    for key, value in data.items():
        if key not in ['ship_id', 'imo_number'] and hasattr(ship, key):
            setattr(ship, key, value)

    ship.updated_at = datetime.utcnow()
    db.session.commit()

    return success_response(ship.to_dict(), 'Ship updated successfully')


@ships_bp.route('/<int:ship_id>', methods=['DELETE'])
@jwt_required()
def delete_ship(ship_id):
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if not user or not user.has_permission('ships.delete'):
        raise AuthorizationError('Insufficient permissions')

    ship = Ship.query.get(ship_id)
    if not ship:
        raise NotFoundError('Ship not found')

    db.session.delete(ship)
    db.session.commit()

    return success_response(None, 'Ship deleted successfully')


@ships_bp.route('/<int:ship_id>/arrival', methods=['POST'])
@jwt_required()
def record_arrival(ship_id):
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if not user or not user.has_permission('ships.write'):
        raise AuthorizationError('Insufficient permissions')

    ship = Ship.query.get(ship_id)
    if not ship:
        raise NotFoundError('Ship not found')

    ship.status = ShipStatus.AT_BERTH
    ship.ata = datetime.utcnow()
    if not ship.current_berth and 'berth' in request.get_json() or {}:
        ship.current_berth = request.get_json()['berth']
    ship.updated_at = datetime.utcnow()
    db.session.commit()

    return success_response(ship.to_dict(), 'Arrival recorded')


@ships_bp.route('/<int:ship_id>/departure', methods=['POST'])
@jwt_required()
def record_departure(ship_id):
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if not user or not user.has_permission('ships.write'):
        raise AuthorizationError('Insufficient permissions')

    ship = Ship.query.get(ship_id)
    if not ship:
        raise NotFoundError('Ship not found')

    ship.status = ShipStatus.DEPARTED
    ship.atd = datetime.utcnow()
    ship.current_berth = None
    ship.updated_at = datetime.utcnow()
    db.session.commit()

    return success_response(ship.to_dict(), 'Departure recorded')


@ships_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_ship_stats():
    total = Ship.query.count()
    by_status = db.session.query(Ship.status, func.count(Ship.id)).group_by(Ship.status).all()
    by_type = db.session.query(Ship.vessel_type, func.count(Ship.id)).group_by(Ship.vessel_type).all()
    by_berth = db.session.query(Ship.current_berth, func.count(Ship.id)).filter(Ship.current_berth.isnot(None)).group_by(Ship.current_berth).all()

    return success_response({
        'total': total,
        'by_status': {s.value: c for s, c in by_status},
        'by_type': {t.value: c for t, c in by_type},
        'by_berth': {b: c for b, c in by_berth if b}
    })


@ships_bp.route('/arrivals-chart', methods=['GET'])
@jwt_required()
def get_arrivals_chart():
    days = request.args.get('days', 30, type=int)
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    arrivals = db.session.query(
        func.date(Ship.ata).label('date'),
        func.count(Ship.id).label('count')
    ).filter(
        Ship.ata >= start_date,
        Ship.ata.isnot(None)
    ).group_by(func.date(Ship.ata)).all()

    departures = db.session.query(
        func.date(Ship.atd).label('date'),
        func.count(Ship.id).label('count')
    ).filter(
        Ship.atd >= start_date,
        Ship.atd.isnot(None)
    ).group_by(func.date(Ship.atd)).all()

    labels = []
    arrival_data = []
    departure_data = []
    current = start_date
    while current <= end_date:
        labels.append(current.strftime('%b %d'))
        arr = next((a for a in arrivals if a.date == current.date()), None)
        dep = next((d for d in departures if d.date == current.date()), None)
        arrival_data.append(arr.count if arr else 0)
        departure_data.append(dep.count if dep else 0)
        current += timedelta(days=1)

    return success_response({
        'labels': labels,
        'datasets': [
            {'label': 'Arrivals', 'data': arrival_data, 'borderColor': 'rgba(13, 110, 253, 1)', 'backgroundColor': 'rgba(13, 110, 253, 0.1)', 'fill': True, 'tension': 0.4},
            {'label': 'Departures', 'data': departure_data, 'borderColor': 'rgba(25, 135, 84, 1)', 'backgroundColor': 'rgba(25, 135, 84, 0.1)', 'fill': True, 'tension': 0.4}
        ]
    })