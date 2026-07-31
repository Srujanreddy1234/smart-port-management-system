from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app.extensions import db
from app.models import (
    User,
    Equipment, EquipmentType, EquipmentStatus,
    MaintenanceType, MaintenancePriority, MaintenanceStatus
)
from app.models.maintenance import MaintenanceSchedule
from app.utils.exceptions import AuthorizationError, NotFoundError, ValidationError as AppValidationError
from app.utils.helpers import success_response, paginate_query
from sqlalchemy import func, or_, and_, desc, asc
from datetime import datetime, timedelta
from marshmallow import Schema, fields, validate, ValidationError


maintenance_bp = Blueprint('maintenance', __name__, url_prefix='/api/v1/maintenance')


class EquipmentSchema(Schema):
    equipment_id = fields.Str(required=True, validate=validate.Length(max=50))
    name = fields.Str(required=True, validate=validate.Length(max=255))
    equipment_type = fields.Str(required=True, validate=validate.OneOf([t.value for t in EquipmentType]))
    manufacturer = fields.Str(validate=validate.Length(max=255))
    model = fields.Str(validate=validate.Length(max=255))
    serial_number = fields.Str(validate=validate.Length(max=255))
    year_manufactured = fields.Int()
    location = fields.Str(validate=validate.Length(max=255))
    zone = fields.Str(validate=validate.Length(max=100))
    status = fields.Str(validate=validate.OneOf([s.value for s in EquipmentStatus]))
    health_percentage = fields.Int(validate=validate.Range(min=0, max=100))
    operating_hours = fields.Float()
    last_service_date = fields.DateTime()
    next_service_date = fields.DateTime()
    last_inspection_date = fields.DateTime()
    next_inspection_date = fields.DateTime()
    warranty_expiry = fields.DateTime()
    specifications = fields.Dict()
    maintenance_interval_hours = fields.Float()
    inspection_interval_days = fields.Int()
    notes = fields.Str()


equipment_schema = EquipmentSchema()
equipment_list_schema = EquipmentSchema(many=True)


class MaintenanceScheduleSchema(Schema):
    equipment_id = fields.Int(required=True)
    maintenance_type = fields.Str(required=True, validate=validate.OneOf([t.value for t in MaintenanceType]))
    priority = fields.Str(validate=validate.OneOf([p.value for p in MaintenancePriority]))
    status = fields.Str(validate=validate.OneOf([s.value for s in MaintenanceStatus]))
    title = fields.Str(required=True, validate=validate.Length(max=255))
    description = fields.Str()
    scheduled_date = fields.DateTime(required=True)
    estimated_duration_hours = fields.Float()
    actual_duration_hours = fields.Float()
    assigned_technician_id = fields.Int()
    supervisor_id = fields.Int()
    started_at = fields.DateTime()
    completed_at = fields.DateTime()
    cost_estimate = fields.Float()
    actual_cost = fields.Float()
    parts_used = fields.Dict()
    work_performed = fields.Str()
    findings = fields.Str()
    recommendations = fields.Str()
    next_maintenance_date = fields.DateTime()
    next_maintenance_type = fields.Str(validate=validate.OneOf([t.value for t in MaintenanceType]))
    is_recurring = fields.Bool()
    recurrence_pattern = fields.Dict()


maintenance_schedule_schema = MaintenanceScheduleSchema()
maintenance_schedules_schema = MaintenanceScheduleSchema(many=True)


def check_permission(permission):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user or not user.has_permission(permission):
        raise AuthorizationError(f'Permission required: {permission}')
    return user


@maintenance_bp.route('', methods=['GET'])
@jwt_required()
def list_equipment():
    check_permission('maintenance.read')

    query = Equipment.query

    search = request.args.get('search', '').strip()
    if search:
        query = query.filter(or_(
            Equipment.equipment_id.ilike(f'%{search}%'),
            Equipment.name.ilike(f'%{search}%'),
            Equipment.manufacturer.ilike(f'%{search}%'),
            Equipment.model.ilike(f'%{search}%')
        ))

    status = request.args.get('status')
    if status:
        try:
            query = query.filter(Equipment.status == EquipmentStatus(status))
        except ValueError:
            raise AppValidationError(f'Invalid status: {status}')

    equipment_type = request.args.get('equipment_type')
    if equipment_type:
        try:
            query = query.filter(Equipment.equipment_type == EquipmentType(equipment_type))
        except ValueError:
            raise AppValidationError(f'Invalid equipment type: {equipment_type}')

    if request.args.get('location'):
        query = query.filter(Equipment.location.ilike(f"%{request.args['location']}%"))
    if request.args.get('zone'):
        query = query.filter(Equipment.zone.ilike(f"%{request.args['zone']}%"))

    sort_by = request.args.get('sort_by', 'created_at')
    sort_order = request.args.get('sort_order', 'desc')
    sort_column = getattr(Equipment, sort_by, Equipment.created_at)
    if sort_order == 'desc':
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(asc(sort_column))

    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return success_response({
        'items': [e.to_dict() for e in pagination.items],
        'total': pagination.total,
        'page': pagination.page,
        'per_page': pagination.per_page,
        'pages': pagination.pages,
        'has_next': pagination.has_next,
        'has_prev': pagination.has_prev
    })


@maintenance_bp.route('/<int:equipment_id>', methods=['GET'])
@jwt_required()
def get_equipment(equipment_id):
    check_permission('maintenance.read')
    equipment = Equipment.query.get(equipment_id)
    if not equipment:
        raise NotFoundError('Equipment not found')
    return success_response(equipment.to_dict())


@maintenance_bp.route('', methods=['POST'])
@jwt_required()
def create_equipment():
    user = check_permission('maintenance.write')

    try:
        data = equipment_schema.load(request.get_json() or {})
    except ValidationError as err:
        raise AppValidationError('Validation failed', details=err.messages)

    if Equipment.query.filter_by(equipment_id=data['equipment_id']).first():
        raise AppValidationError('Equipment ID already exists')

    if data.get('serial_number') and Equipment.query.filter_by(serial_number=data['serial_number']).first():
        raise AppValidationError('Serial number already exists')

    equipment = Equipment(**data)
    db.session.add(equipment)
    db.session.commit()

    return success_response(equipment.to_dict(), 'Equipment created successfully', 201)


@maintenance_bp.route('/<int:equipment_id>', methods=['PUT'])
@jwt_required()
def update_equipment(equipment_id):
    user = check_permission('maintenance.write')
    equipment = Equipment.query.get(equipment_id)
    if not equipment:
        raise NotFoundError('Equipment not found')

    try:
        data = equipment_schema.load(request.get_json() or {}, partial=True)
    except ValidationError as err:
        raise AppValidationError('Validation failed', details=err.messages)

    if 'equipment_id' in data and data['equipment_id'] != equipment.equipment_id:
        if Equipment.query.filter_by(equipment_id=data['equipment_id']).first():
            raise AppValidationError('Equipment ID already exists')
        equipment.equipment_id = data['equipment_id']

    if 'serial_number' in data and data['serial_number'] != equipment.serial_number:
        if data['serial_number'] and Equipment.query.filter_by(serial_number=data['serial_number']).first():
            raise AppValidationError('Serial number already exists')
        equipment.serial_number = data['serial_number']

    for key, value in data.items():
        if key not in ['equipment_id', 'serial_number'] and hasattr(equipment, key):
            setattr(equipment, key, value)

    equipment.updated_at = datetime.utcnow()
    db.session.commit()

    return success_response(equipment.to_dict(), 'Equipment updated successfully')


@maintenance_bp.route('/<int:equipment_id>', methods=['DELETE'])
@jwt_required()
def delete_equipment(equipment_id):
    user = check_permission('maintenance.delete')
    equipment = Equipment.query.get(equipment_id)
    if not equipment:
        raise NotFoundError('Equipment not found')

    db.session.delete(equipment)
    db.session.commit()
    return success_response(None, 'Equipment deleted successfully')


@maintenance_bp.route('/schedules', methods=['GET'])
@jwt_required()
def list_maintenance_schedules():
    check_permission('maintenance.read')

    query = MaintenanceSchedule.query

    search = request.args.get('search', '').strip()
    if search:
        query = query.filter(or_(
            MaintenanceSchedule.title.ilike(f'%{search}%'),
            MaintenanceSchedule.description.ilike(f'%{search}%'),
            MaintenanceSchedule.work_performed.ilike(f'%{search}%')
        ))

    status = request.args.get('status')
    if status:
        try:
            query = query.filter(MaintenanceSchedule.status == MaintenanceStatus(status))
        except ValueError:
            raise AppValidationError(f'Invalid status: {status}')

    priority = request.args.get('priority')
    if priority:
        try:
            query = query.filter(MaintenanceSchedule.priority == MaintenancePriority(priority))
        except ValueError:
            raise AppValidationError(f'Invalid priority: {priority}')

    if request.args.get('equipment_id'):
        query = query.filter(MaintenanceSchedule.equipment_id == request.args['equipment_id'])

    maintenance_type = request.args.get('maintenance_type')
    if maintenance_type:
        try:
            query = query.filter(MaintenanceSchedule.maintenance_type == MaintenanceType(maintenance_type))
        except ValueError:
            raise AppValidationError(f'Invalid maintenance type: {maintenance_type}')

    if request.args.get('assigned_technician_id'):
        query = query.filter(MaintenanceSchedule.assigned_technician_id == request.args['assigned_technician_id'])

    sort_by = request.args.get('sort_by', 'scheduled_date')
    sort_order = request.args.get('sort_order', 'desc')
    sort_column = getattr(MaintenanceSchedule, sort_by, MaintenanceSchedule.scheduled_date)
    if sort_order == 'desc':
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(asc(sort_column))

    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return success_response({
        'items': [s.to_dict() for s in pagination.items],
        'total': pagination.total,
        'page': pagination.page,
        'per_page': pagination.per_page,
        'pages': pagination.pages,
        'has_next': pagination.has_next,
        'has_prev': pagination.has_prev
    })


@maintenance_bp.route('/schedules/<int:schedule_id>', methods=['GET'])
@jwt_required()
def get_maintenance_schedule(schedule_id):
    check_permission('maintenance.read')
    schedule = MaintenanceSchedule.query.get(schedule_id)
    if not schedule:
        raise NotFoundError('Maintenance schedule not found')
    return success_response(schedule.to_dict())


@maintenance_bp.route('/schedules', methods=['POST'])
@jwt_required()
def create_maintenance_schedule():
    user = check_permission('maintenance.write')

    try:
        data = maintenance_schedule_schema.load(request.get_json() or {})
    except ValidationError as err:
        raise AppValidationError('Validation failed', details=err.messages)

    equipment = Equipment.query.get(data['equipment_id'])
    if not equipment:
        raise NotFoundError('Equipment not found')

    if data.get('assigned_technician_id'):
        technician = User.query.get(data['assigned_technician_id'])
        if not technician:
            raise NotFoundError('Assigned technician not found')

    if data.get('supervisor_id'):
        supervisor = User.query.get(data['supervisor_id'])
        if not supervisor:
            raise NotFoundError('Supervisor not found')

    schedule = MaintenanceSchedule(**data)
    db.session.add(schedule)
    db.session.commit()

    return success_response(schedule.to_dict(), 'Maintenance schedule created successfully', 201)


@maintenance_bp.route('/schedules/<int:schedule_id>', methods=['PUT'])
@jwt_required()
def update_maintenance_schedule(schedule_id):
    user = check_permission('maintenance.write')
    schedule = MaintenanceSchedule.query.get(schedule_id)
    if not schedule:
        raise NotFoundError('Maintenance schedule not found')

    try:
        data = maintenance_schedule_schema.load(request.get_json() or {}, partial=True)
    except ValidationError as err:
        raise AppValidationError('Validation failed', details=err.messages)

    if 'equipment_id' in data and data['equipment_id'] != schedule.equipment_id:
        equipment = Equipment.query.get(data['equipment_id'])
        if not equipment:
            raise NotFoundError('Equipment not found')
        schedule.equipment_id = data['equipment_id']

    if 'assigned_technician_id' in data:
        if data['assigned_technician_id']:
            technician = User.query.get(data['assigned_technician_id'])
            if not technician:
                raise NotFoundError('Assigned technician not found')
        schedule.assigned_technician_id = data['assigned_technician_id']

    if 'supervisor_id' in data:
        if data['supervisor_id']:
            supervisor = User.query.get(data['supervisor_id'])
            if not supervisor:
                raise NotFoundError('Supervisor not found')
        schedule.supervisor_id = data['supervisor_id']

    for key, value in data.items():
        if key not in ['equipment_id', 'assigned_technician_id', 'supervisor_id'] and hasattr(schedule, key):
            setattr(schedule, key, value)

    schedule.updated_at = datetime.utcnow()
    db.session.commit()

    return success_response(schedule.to_dict(), 'Maintenance schedule updated successfully')
