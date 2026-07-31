from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app.extensions import db
from app.models import User, Truck, TruckStatus, TruckType, Container
from app.utils.exceptions import AuthorizationError, NotFoundError, ValidationError as AppValidationError
from app.utils.helpers import success_response, paginate_query
from sqlalchemy import func, or_, and_, desc, asc
from datetime import datetime, timedelta
from marshmallow import Schema, fields, validate, ValidationError


trucks_bp = Blueprint('trucks', __name__, url_prefix='/api/v1/trucks')


class TruckSchema(Schema):
    truck_number = fields.Str(required=True, validate=validate.Length(max=50))
    driver_name = fields.Str(validate=validate.Length(max=255))
    driver_phone = fields.Str(validate=validate.Length(max=20))
    truck_type = fields.Str(required=True, validate=validate.OneOf([t.value for t in TruckType]))
    status = fields.Str(validate=validate.OneOf([s.value for s in TruckStatus]))
    capacity = fields.Int()
    license_plate = fields.Str(validate=validate.Length(max=50))
    chassis_number = fields.Str(validate=validate.Length(max=50))
    owner = fields.Str(validate=validate.Length(max=255))
    owner_contact = fields.Str(validate=validate.Length(max=255))
    assigned_container_id = fields.Int()
    current_location = fields.Str(validate=validate.Length(max=255))
    gate_in_time = fields.DateTime()
    gate_out_time = fields.DateTime()
    assigned_at = fields.DateTime()


truck_schema = TruckSchema()
trucks_schema = TruckSchema(many=True)


def check_permission(permission):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user or not user.has_permission(permission):
        raise AuthorizationError(f'Permission required: {permission}')
    return user


@trucks_bp.route('', methods=['GET'])
@jwt_required()
def list_trucks():
    check_permission('trucks.read')

    query = Truck.query

    search = request.args.get('search', '').strip()
    if search:
        query = query.filter(or_(
            Truck.truck_number.ilike(f'%{search}%'),
            Truck.driver_name.ilike(f'%{search}%'),
            Truck.owner.ilike(f'%{search}%'),
            Truck.license_plate.ilike(f'%{search}%')
        ))

    status = request.args.get('status')
    if status:
        try:
            query = query.filter(Truck.status == TruckStatus(status))
        except ValueError:
            raise AppValidationError(f'Invalid status: {status}')

    truck_type = request.args.get('truck_type')
    if truck_type:
        try:
            query = query.filter(Truck.truck_type == TruckType(truck_type))
        except ValueError:
            raise AppValidationError(f'Invalid truck type: {truck_type}')

    if request.args.get('current_location'):
        query = query.filter(Truck.current_location.ilike(f"%{request.args['current_location']}%"))
    if request.args.get('assigned_container_id'):
        query = query.filter(Truck.assigned_container_id == request.args['assigned_container_id'])

    sort_by = request.args.get('sort_by', 'created_at')
    sort_order = request.args.get('sort_order', 'desc')
    sort_column = getattr(Truck, sort_by, Truck.created_at)
    if sort_order == 'desc':
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(asc(sort_column))

    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return success_response({
        'items': [t.to_dict() for t in pagination.items],
        'total': pagination.total,
        'page': pagination.page,
        'per_page': pagination.per_page,
        'pages': pagination.pages,
        'has_next': pagination.has_next,
        'has_prev': pagination.has_prev
    })


@trucks_bp.route('/<int:truck_id>', methods=['GET'])
@jwt_required()
def get_truck(truck_id):
    check_permission('trucks.read')
    truck = Truck.query.get(truck_id)
    if not truck:
        raise NotFoundError('Truck not found')
    return success_response(truck.to_dict())


@trucks_bp.route('', methods=['POST'])
@jwt_required()
def create_truck():
    user = check_permission('trucks.write')

    try:
        data = truck_schema.load(request.get_json() or {})
    except ValidationError as err:
        raise AppValidationError('Validation failed', details=err.messages)

    if Truck.query.filter_by(truck_number=data['truck_number']).first():
        raise AppValidationError('Truck number already exists')

    if data.get('license_plate') and Truck.query.filter_by(license_plate=data['license_plate']).first():
        raise AppValidationError('License plate already exists')

    if data.get('assigned_container_id'):
        container = Container.query.get(data['assigned_container_id'])
        if not container:
            raise NotFoundError('Container not found')

    truck = Truck(**data)
    db.session.add(truck)
    db.session.commit()

    return success_response(truck.to_dict(), 'Truck created successfully', 201)


@trucks_bp.route('/<int:truck_id>', methods=['PUT'])
@jwt_required()
def update_truck(truck_id):
    user = check_permission('trucks.write')
    truck = Truck.query.get(truck_id)
    if not truck:
        raise NotFoundError('Truck not found')

    try:
        data = truck_schema.load(request.get_json() or {}, partial=True)
    except ValidationError as err:
        raise AppValidationError('Validation failed', details=err.messages)

    if 'truck_number' in data and data['truck_number'] != truck.truck_number:
        if Truck.query.filter_by(truck_number=data['truck_number']).first():
            raise AppValidationError('Truck number already exists')
        truck.truck_number = data['truck_number']

    if 'license_plate' in data and data['license_plate'] != truck.license_plate:
        if data['license_plate'] and Truck.query.filter_by(license_plate=data['license_plate']).first():
            raise AppValidationError('License plate already exists')
        truck.license_plate = data['license_plate']

    if 'assigned_container_id' in data:
        if data['assigned_container_id']:
            container = Container.query.get(data['assigned_container_id'])
            if not container:
                raise NotFoundError('Container not found')
        truck.assigned_container_id = data['assigned_container_id']

    for key, value in data.items():
        if key not in ['truck_number', 'license_plate', 'assigned_container_id'] and hasattr(truck, key):
            setattr(truck, key, value)

    truck.updated_at = datetime.utcnow()
    db.session.commit()

    return success_response(truck.to_dict(), 'Truck updated successfully')


@trucks_bp.route('/<int:truck_id>', methods=['DELETE'])
@jwt_required()
def delete_truck(truck_id):
    user = check_permission('trucks.delete')
    truck = Truck.query.get(truck_id)
    if not truck:
        raise NotFoundError('Truck not found')

    db.session.delete(truck)
    db.session.commit()
    return success_response(None, 'Truck deleted successfully')


@trucks_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_truck_stats():
    check_permission('trucks.read')

    total = Truck.query.count()
    by_status = db.session.query(Truck.status, func.count(Truck.id)).group_by(Truck.status).all()
    by_type = db.session.query(Truck.truck_type, func.count(Truck.id)).group_by(Truck.truck_type).all()

    return success_response({
        'total': total,
        'by_status': {s.value: c for s, c in by_status},
        'by_type': {t.value: c for t, c in by_type}
    })
