from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app.extensions import db
from app.models import (
    User,
    SecurityIncident, IncidentType, IncidentSeverity, IncidentStatus,
    SecurityZone, Alert, AlertType, Camera
)
from app.utils.exceptions import AuthorizationError, NotFoundError, ValidationError as AppValidationError
from app.utils.helpers import success_response, paginate_query
from sqlalchemy import func, or_, and_, desc, asc
from datetime import datetime, timedelta
from marshmallow import Schema, fields, validate, ValidationError


security_bp = Blueprint('security', __name__, url_prefix='/api/v1/security')


class IncidentSchema(Schema):
    incident_id = fields.Str(required=True, validate=validate.Length(max=50))
    incident_type = fields.Str(required=True, validate=validate.OneOf([t.value for t in IncidentType]))
    zone = fields.Str(required=True, validate=validate.OneOf([z.value for z in SecurityZone]))
    severity = fields.Str(required=True, validate=validate.OneOf([s.value for s in IncidentSeverity]))
    status = fields.Str(validate=validate.OneOf([s.value for s in IncidentStatus]))
    title = fields.Str(required=True, validate=validate.Length(max=255))
    description = fields.Str()
    location_details = fields.Str(validate=validate.Length(max=500))
    reported_by = fields.Str(validate=validate.Length(max=255))
    assigned_officer_id = fields.Int()
    camera_id = fields.Str(validate=validate.Length(max=50))
    camera_footage_url = fields.Str(validate=validate.Length(max=500))
    detected_at = fields.DateTime()
    acknowledged_at = fields.DateTime()
    resolved_at = fields.DateTime()
    closed_at = fields.DateTime()
    resolution_notes = fields.Str()
    response_time_minutes = fields.Int()
    is_false_alarm = fields.Bool()


incident_schema = IncidentSchema()
incidents_schema = IncidentSchema(many=True)


def check_permission(permission):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user or not user.has_permission(permission):
        raise AuthorizationError(f'Permission required: {permission}')
    return user


@security_bp.route('', methods=['GET'])
@jwt_required()
def list_incidents():
    check_permission('security.read')

    query = SecurityIncident.query

    search = request.args.get('search', '').strip()
    if search:
        query = query.filter(or_(
            SecurityIncident.incident_id.ilike(f'%{search}%'),
            SecurityIncident.title.ilike(f'%{search}%'),
            SecurityIncident.description.ilike(f'%{search}%'),
            SecurityIncident.location_details.ilike(f'%{search}%')
        ))

    status = request.args.get('status')
    if status:
        try:
            query = query.filter(SecurityIncident.status == IncidentStatus(status))
        except ValueError:
            raise AppValidationError(f'Invalid status: {status}')

    severity = request.args.get('severity')
    if severity:
        try:
            query = query.filter(SecurityIncident.severity == IncidentSeverity(severity))
        except ValueError:
            raise AppValidationError(f'Invalid severity: {severity}')

    zone = request.args.get('zone')
    if zone:
        try:
            query = query.filter(SecurityIncident.zone == SecurityZone(zone))
        except ValueError:
            raise AppValidationError(f'Invalid zone: {zone}')

    if request.args.get('incident_type'):
        try:
            query = query.filter(SecurityIncident.incident_type == IncidentType(request.args['incident_type']))
        except ValueError:
            raise AppValidationError(f"Invalid incident type: {request.args['incident_type']}")

    if request.args.get('assigned_officer_id'):
        query = query.filter(SecurityIncident.assigned_officer_id == request.args['assigned_officer_id'])

    sort_by = request.args.get('sort_by', 'detected_at')
    sort_order = request.args.get('sort_order', 'desc')
    sort_column = getattr(SecurityIncident, sort_by, SecurityIncident.detected_at)
    if sort_order == 'desc':
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(asc(sort_column))

    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return success_response({
        'items': [i.to_dict() for i in pagination.items],
        'total': pagination.total,
        'page': pagination.page,
        'per_page': pagination.per_page,
        'pages': pagination.pages,
        'has_next': pagination.has_next,
        'has_prev': pagination.has_prev
    })


@security_bp.route('/<int:incident_id>', methods=['GET'])
@jwt_required()
def get_incident(incident_id):
    check_permission('security.read')
    incident = SecurityIncident.query.get(incident_id)
    if not incident:
        raise NotFoundError('Incident not found')
    return success_response(incident.to_dict())


@security_bp.route('', methods=['POST'])
@jwt_required()
def create_incident():
    user = check_permission('security.write')

    try:
        data = incident_schema.load(request.get_json() or {})
    except ValidationError as err:
        raise AppValidationError('Validation failed', details=err.messages)

    if SecurityIncident.query.filter_by(incident_id=data['incident_id']).first():
        raise AppValidationError('Incident ID already exists')

    if data.get('assigned_officer_id'):
        officer = User.query.get(data['assigned_officer_id'])
        if not officer:
            raise NotFoundError('Assigned officer not found')

    if data.get('camera_id'):
        camera = Camera.query.filter_by(camera_id=data['camera_id']).first()
        if not camera:
            raise NotFoundError('Camera not found')

    incident = SecurityIncident(**data)
    db.session.add(incident)
    db.session.commit()

    return success_response(incident.to_dict(), 'Incident created successfully', 201)


@security_bp.route('/<int:incident_id>', methods=['PUT'])
@jwt_required()
def update_incident(incident_id):
    user = check_permission('security.write')
    incident = SecurityIncident.query.get(incident_id)
    if not incident:
        raise NotFoundError('Incident not found')

    try:
        data = incident_schema.load(request.get_json() or {}, partial=True)
    except ValidationError as err:
        raise AppValidationError('Validation failed', details=err.messages)

    if 'incident_id' in data and data['incident_id'] != incident.incident_id:
        if SecurityIncident.query.filter_by(incident_id=data['incident_id']).first():
            raise AppValidationError('Incident ID already exists')
        incident.incident_id = data['incident_id']

    if 'assigned_officer_id' in data:
        if data['assigned_officer_id']:
            officer = User.query.get(data['assigned_officer_id'])
            if not officer:
                raise NotFoundError('Assigned officer not found')
        incident.assigned_officer_id = data['assigned_officer_id']

    if 'camera_id' in data:
        if data['camera_id']:
            camera = Camera.query.filter_by(camera_id=data['camera_id']).first()
            if not camera:
                raise NotFoundError('Camera not found')
        incident.camera_id = data['camera_id']

    for key, value in data.items():
        if key not in ['incident_id', 'assigned_officer_id', 'camera_id'] and hasattr(incident, key):
            setattr(incident, key, value)

    incident.updated_at = datetime.utcnow()
    db.session.commit()

    return success_response(incident.to_dict(), 'Incident updated successfully')


@security_bp.route('/<int:incident_id>', methods=['DELETE'])
@jwt_required()
def delete_incident(incident_id):
    user = check_permission('security.delete')
    incident = SecurityIncident.query.get(incident_id)
    if not incident:
        raise NotFoundError('Incident not found')

    db.session.delete(incident)
    db.session.commit()
    return success_response(None, 'Incident deleted successfully')


@security_bp.route('/alerts', methods=['GET'])
@jwt_required()
def list_alerts():
    check_permission('security.read')

    query = Alert.query

    search = request.args.get('search', '').strip()
    if search:
        query = query.filter(or_(
            Alert.alert_id.ilike(f'%{search}%'),
            Alert.title.ilike(f'%{search}%'),
            Alert.message.ilike(f'%{search}%')
        ))

    if request.args.get('is_read') is not None:
        query = query.filter(Alert.is_read == (request.args['is_read'].lower() == 'true'))
    if request.args.get('is_acknowledged') is not None:
        query = query.filter(Alert.is_acknowledged == (request.args['is_acknowledged'].lower() == 'true'))

    alert_type = request.args.get('alert_type')
    if alert_type:
        try:
            query = query.filter(Alert.alert_type == AlertType(alert_type))
        except ValueError:
            raise AppValidationError(f'Invalid alert type: {alert_type}')

    severity = request.args.get('severity')
    if severity:
        try:
            query = query.filter(Alert.severity == IncidentSeverity(severity))
        except ValueError:
            raise AppValidationError(f'Invalid severity: {severity}')

    zone = request.args.get('zone')
    if zone:
        try:
            query = query.filter(Alert.zone == SecurityZone(zone))
        except ValueError:
            raise AppValidationError(f'Invalid zone: {zone}')

    sort_by = request.args.get('sort_by', 'created_at')
    sort_order = request.args.get('sort_order', 'desc')
    sort_column = getattr(Alert, sort_by, Alert.created_at)
    if sort_order == 'desc':
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(asc(sort_column))

    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return success_response({
        'items': [a.to_dict() for a in pagination.items],
        'total': pagination.total,
        'page': pagination.page,
        'per_page': pagination.per_page,
        'pages': pagination.pages,
        'has_next': pagination.has_next,
        'has_prev': pagination.has_prev
    })


@security_bp.route('/alerts/<int:alert_id>/acknowledge', methods=['POST'])
@jwt_required()
def acknowledge_alert(alert_id):
    user = check_permission('security.write')

    alert = Alert.query.get(alert_id)
    if not alert:
        raise NotFoundError('Alert not found')

    alert.is_read = True
    alert.is_acknowledged = True
    alert.acknowledged_by_id = user.id
    alert.acknowledged_at = datetime.utcnow()
    db.session.commit()

    return success_response(alert.to_dict(), 'Alert acknowledged successfully')


@security_bp.route('/cameras', methods=['GET'])
@jwt_required()
def list_cameras():
    check_permission('security.read')

    query = Camera.query

    search = request.args.get('search', '').strip()
    if search:
        query = query.filter(or_(
            Camera.camera_id.ilike(f'%{search}%'),
            Camera.name.ilike(f'%{search}%'),
            Camera.location.ilike(f'%{search}%')
        ))

    zone = request.args.get('zone')
    if zone:
        try:
            query = query.filter(Camera.zone == SecurityZone(zone))
        except ValueError:
            raise AppValidationError(f'Invalid zone: {zone}')

    if request.args.get('is_active') is not None:
        query = query.filter(Camera.is_active == (request.args['is_active'].lower() == 'true'))

    sort_by = request.args.get('sort_by', 'created_at')
    sort_order = request.args.get('sort_order', 'desc')
    sort_column = getattr(Camera, sort_by, Camera.created_at)
    if sort_order == 'desc':
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(asc(sort_column))

    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return success_response({
        'items': [c.to_dict() for c in pagination.items],
        'total': pagination.total,
        'page': pagination.page,
        'per_page': pagination.per_page,
        'pages': pagination.pages,
        'has_next': pagination.has_next,
        'has_prev': pagination.has_prev
    })
