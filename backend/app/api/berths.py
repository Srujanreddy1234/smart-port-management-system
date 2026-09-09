from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from marshmallow import Schema, fields, validate, ValidationError
from app.extensions import db
from app.models import Berth, BerthStatus, Ship, ShipStatus, User
from app.utils.exceptions import ValidationError as AppValidationError, NotFoundError, AuthorizationError
from app.utils.helpers import success_response, paginate_query
from sqlalchemy import func, or_, desc
from datetime import datetime


berths_bp = Blueprint('berths', __name__, url_prefix='/api/v1/berths')


class BerthSchema(Schema):
    id = fields.Int(dump_only=True)
    berth_id = fields.Str(required=True, validate=validate.Length(max=50))
    name = fields.Str(required=True, validate=validate.Length(max=255))
    code = fields.Str(required=True, validate=validate.Length(max=20))
    status = fields.Str(validate=validate.OneOf([s.value for s in BerthStatus]))
    max_length = fields.Float()
    max_beam = fields.Float()
    max_draft = fields.Float()
    max_tonnage = fields.Int()
    max_containers = fields.Int()
    depth = fields.Float()
    length = fields.Float()
    has_crane = fields.Bool()
    crane_capacity = fields.Int()
    has_reins = fields.Bool()
    has_power = fields.Bool()
    has_water = fields.Bool()
    zone = fields.Str(validate=validate.Length(max=100))
    terminal = fields.Str(validate=validate.Length(max=100))
    notes = fields.Str()


berth_schema = BerthSchema()
berth_list_schema = BerthSchema(many=True)


@berths_bp.route('', methods=['GET'])
@jwt_required()
def list_berths():
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)
    search = request.args.get('search', '').strip()
    status = request.args.get('status')
    zone = request.args.get('zone')
    terminal = request.args.get('terminal')
    sort_by = request.args.get('sort_by', 'code')
    sort_order = request.args.get('sort_order', 'asc')

    query = Berth.query

    if search:
        query = query.filter(or_(
            Berth.name.ilike(f'%{search}%'),
            Berth.code.ilike(f'%{search}%'),
            Berth.berth_id.ilike(f'%{search}%'),
        ))

    if status:
        try:
            query = query.filter(Berth.status == BerthStatus(status))
        except ValueError:
            raise AppValidationError(f'Invalid status: {status}')

    if zone:
        query = query.filter(Berth.zone == zone)

    if terminal:
        query = query.filter(Berth.terminal == terminal)

    sort_column = getattr(Berth, sort_by, Berth.code)
    if sort_order == 'desc':
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(sort_column)

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return success_response({
        'items': [berth.to_dict() for berth in pagination.items],
        'total': pagination.total,
        'page': pagination.page,
        'per_page': pagination.per_page,
        'pages': pagination.pages,
        'has_next': pagination.has_next,
        'has_prev': pagination.has_prev
    })


@berths_bp.route('/<int:berth_id>', methods=['GET'])
@jwt_required()
def get_berth(berth_id):
    berth = Berth.query.get(berth_id)
    if not berth:
        raise NotFoundError('Berth not found')
    return success_response(berth.to_dict())


@berths_bp.route('', methods=['POST'])
@jwt_required()
def create_berth():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if not user or not user.has_permission('berths.write'):
        raise AuthorizationError('Insufficient permissions')

    try:
        data = berth_schema.load(request.get_json() or {})
    except ValidationError as err:
        return jsonify({'success': False, 'errors': err.messages}), 400

    if Berth.query.filter_by(berth_id=data['berth_id']).first():
        raise AppValidationError('Berth ID already exists')
    if Berth.query.filter_by(code=data['code']).first():
        raise AppValidationError('Berth code already exists')

    berth = Berth(**data)
    db.session.add(berth)
    db.session.commit()

    return success_response(berth.to_dict(), 'Berth created successfully', 201)


@berths_bp.route('/<int:berth_id>', methods=['PUT'])
@jwt_required()
def update_berth(berth_id):
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if not user or not user.has_permission('berths.write'):
        raise AuthorizationError('Insufficient permissions')

    berth = Berth.query.get(berth_id)
    if not berth:
        raise NotFoundError('Berth not found')

    try:
        data = berth_schema.load(request.get_json() or {}, partial=True)
    except ValidationError as err:
        return jsonify({'success': False, 'errors': err.messages}), 400

    if 'berth_id' in data and data['berth_id'] != berth.berth_id:
        if Berth.query.filter_by(berth_id=data['berth_id']).first():
            raise AppValidationError('Berth ID already exists')
        berth.berth_id = data['berth_id']

    if 'code' in data and data['code'] != berth.code:
        if Berth.query.filter_by(code=data['code']).first():
            raise AppValidationError('Berth code already exists')
        berth.code = data['code']

    for key, value in data.items():
        if key not in ['berth_id', 'code'] and hasattr(berth, key):
            setattr(berth, key, value)

    berth.updated_at = datetime.utcnow()
    db.session.commit()

    return success_response(berth.to_dict(), 'Berth updated successfully')


@berths_bp.route('/<int:berth_id>', methods=['DELETE'])
@jwt_required()
def delete_berth(berth_id):
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if not user or not user.has_permission('berths.delete'):
        raise AuthorizationError('Insufficient permissions')

    berth = Berth.query.get(berth_id)
    if not berth:
        raise NotFoundError('Berth not found')

    if berth.current_ship_id:
        raise AppValidationError('Cannot delete berth with assigned ship')

    db.session.delete(berth)
    db.session.commit()

    return success_response(None, 'Berth deleted successfully')


@berths_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_berth_stats():
    total = Berth.query.count()
    by_status = db.session.query(Berth.status, func.count(Berth.id)).group_by(Berth.status).all()
    by_zone = db.session.query(Berth.zone, func.count(Berth.id)).filter(Berth.zone.isnot(None)).group_by(Berth.zone).all()
    by_terminal = db.session.query(Berth.terminal, func.count(Berth.id)).filter(Berth.terminal.isnot(None)).group_by(Berth.terminal).all()

    occupied_count = sum(c for s, c in by_status if s == BerthStatus.OCCUPIED)
    occupancy_rate = (occupied_count / total * 100) if total > 0 else 0

    return success_response({
        'total': total,
        'occupied': occupied_count,
        'available': sum(c for s, c in by_status if s == BerthStatus.AVAILABLE),
        'maintenance': sum(c for s, c in by_status if s == BerthStatus.MAINTENANCE),
        'occupancy_rate': round(occupancy_rate, 1),
        'by_status': {s.value: c for s, c in by_status},
        'by_zone': {z: c for z, c in by_zone if z},
        'by_terminal': {t: c for t, c in by_terminal if t}
    })


@berths_bp.route('/<int:berth_id>/assign', methods=['POST'])
@jwt_required()
def assign_ship(berth_id):
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if not user or not user.has_permission('berths.write'):
        raise AuthorizationError('Insufficient permissions')

    berth = Berth.query.get(berth_id)
    if not berth:
        raise NotFoundError('Berth not found')

    data = request.get_json() or {}
    ship_id = data.get('ship_id')
    if not ship_id:
        raise AppValidationError('Ship ID required')

    ship = Ship.query.get(ship_id)
    if not ship:
        raise NotFoundError('Ship not found')

    can_accommodate, message = berth.can_accommodate(ship)
    if not can_accommodate:
        raise AppValidationError(message)

    if berth.current_ship_id:
        raise AppValidationError('Berth already occupied')

    old_berth_name = ship.current_berth
    ship.current_berth = berth.name
    ship.status = ShipStatus.AT_BERTH
    ship.ata = datetime.utcnow()
    berth.current_ship_id = ship.id
    berth.status = BerthStatus.OCCUPIED
    berth.occupied_since = datetime.utcnow()

    from app.api.sse import publish_event
    from app.models.event_log import EventType, EventSeverity
    publish_event(
        event_type=EventType.BERTH_ASSIGNMENT,
        title=f'{ship.name} assigned to {berth.name}',
        entity_type='berth',
        entity_id=berth.id,
        user_id=current_user_id,
        severity=EventSeverity.INFO,
        data={'ship_name': ship.name, 'berth_name': berth.name},
    )

    db.session.commit()

    return success_response({
        'berth': berth.to_dict(),
        'ship': ship.to_dict()
    }, f'Ship assigned to {berth.name}')


@berths_bp.route('/<int:berth_id>/release', methods=['POST'])
@jwt_required()
def release_berth(berth_id):
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if not user or not user.has_permission('berths.write'):
        raise AuthorizationError('Insufficient permissions')

    berth = Berth.query.get(berth_id)
    if not berth:
        raise NotFoundError('Berth not found')

    if not berth.current_ship_id:
        raise AppValidationError('Berth is not occupied')

    ship = Ship.query.get(berth.current_ship_id)
    if ship:
        ship.current_berth = None
        ship.status = ShipStatus.DEPARTED
        ship.atd = datetime.utcnow()

    berth.current_ship_id = None
    berth.status = BerthStatus.AVAILABLE
    berth.occupied_since = None

    from app.api.sse import publish_event
    from app.models.event_log import EventType
    publish_event(
        event_type=EventType.BERTH_RELEASE,
        title=f'{berth.name} released',
        entity_type='berth',
        entity_id=berth.id,
        user_id=current_user_id,
        data={'berth_name': berth.name, 'ship_name': ship.name if ship else None},
    )

    db.session.commit()

    return success_response({
        'berth': berth.to_dict(),
        'ship': ship.to_dict() if ship else None
    }, 'Berth released')


@berths_bp.route('/available', methods=['GET'])
@jwt_required()
def get_available_berths():
    length = request.args.get('length', type=float)
    beam = request.args.get('beam', type=float)
    draft = request.args.get('draft', type=float)
    tonnage = request.args.get('tonnage', type=int)

    query = Berth.query.filter(Berth.status.in_([BerthStatus.AVAILABLE, BerthStatus.RESERVED]))

    available = []
    for berth in query.all():
        can_fit = True
        reasons = []
        if length and berth.max_length and length > berth.max_length:
            can_fit = False
            reasons.append(f'length {length} > max {berth.max_length}')
        if beam and berth.max_beam and beam > berth.max_beam:
            can_fit = False
            reasons.append(f'beam {beam} > max {berth.max_beam}')
        if draft and berth.max_draft and draft > berth.max_draft:
            can_fit = False
            reasons.append(f'draft {draft} > max {berth.max_draft}')
        if tonnage and berth.max_tonnage and tonnage > berth.max_tonnage:
            can_fit = False
            reasons.append(f'tonnage {tonnage} > max {berth.max_tonnage}')

        if can_fit:
            b = berth.to_dict()
            b['fit_reasons'] = reasons
            available.append(b)

    return success_response({'available_berths': available, 'count': len(available)})