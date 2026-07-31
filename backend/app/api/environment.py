from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app.extensions import db
from app.models import (
    User,
    MonitoringStation,
    AirQualityReading,
    WaterQualityReading,
    NoiseReading,
    WeatherReading,
    EnvironmentalAlert
)
from app.utils.exceptions import AuthorizationError, NotFoundError, ValidationError as AppValidationError
from app.utils.helpers import success_response, paginate_query
from sqlalchemy import func, or_, and_, desc, asc
from datetime import datetime, timedelta
from marshmallow import Schema, fields, validate, ValidationError


environment_bp = Blueprint('environment', __name__, url_prefix='/api/v1/environment')


class MonitoringStationSchema(Schema):
    station_id = fields.Str(required=True, validate=validate.Length(max=50))
    name = fields.Str(required=True, validate=validate.Length(max=255))
    station_type = fields.Str(required=True, validate=validate.Length(max=50))
    latitude = fields.Float()
    longitude = fields.Float()
    zone = fields.Str(validate=validate.Length(max=100))
    address = fields.Str(validate=validate.Length(max=500))
    elevation = fields.Float()
    is_active = fields.Bool()
    parameters = fields.Dict()
    station_reading_alert_compliance_metadata = fields.Dict(data_key='metadata')


monitoring_station_schema = MonitoringStationSchema()
monitoring_stations_schema = MonitoringStationSchema(many=True)


def check_permission(permission):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user or not user.has_permission(permission):
        raise AuthorizationError(f'Permission required: {permission}')
    return user


@environment_bp.route('', methods=['GET'])
@jwt_required()
def list_stations():
    check_permission('environment.read')

    query = MonitoringStation.query

    search = request.args.get('search', '').strip()
    if search:
        query = query.filter(or_(
            MonitoringStation.station_id.ilike(f'%{search}%'),
            MonitoringStation.name.ilike(f'%{search}%'),
            MonitoringStation.zone.ilike(f'%{search}%'),
            MonitoringStation.address.ilike(f'%{search}%')
        ))

    if request.args.get('station_type'):
        query = query.filter(MonitoringStation.station_type.ilike(f"%{request.args['station_type']}%"))
    if request.args.get('zone'):
        query = query.filter(MonitoringStation.zone.ilike(f"%{request.args['zone']}%"))
    if request.args.get('is_active') is not None:
        query = query.filter(MonitoringStation.is_active == (request.args['is_active'].lower() == 'true'))

    sort_by = request.args.get('sort_by', 'created_at')
    sort_order = request.args.get('sort_order', 'desc')
    sort_column = getattr(MonitoringStation, sort_by, MonitoringStation.created_at)
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


@environment_bp.route('/<int:station_id>', methods=['GET'])
@jwt_required()
def get_station(station_id):
    check_permission('environment.read')
    station = MonitoringStation.query.get(station_id)
    if not station:
        raise NotFoundError('Monitoring station not found')
    return success_response(station.to_dict())


@environment_bp.route('', methods=['POST'])
@jwt_required()
def create_station():
    user = check_permission('environment.write')

    try:
        data = monitoring_station_schema.load(request.get_json() or {})
    except ValidationError as err:
        raise AppValidationError('Validation failed', details=err.messages)

    if MonitoringStation.query.filter_by(station_id=data['station_id']).first():
        raise AppValidationError('Station ID already exists')

    station = MonitoringStation(**data)
    db.session.add(station)
    db.session.commit()

    return success_response(station.to_dict(), 'Monitoring station created successfully', 201)


@environment_bp.route('/<int:station_id>', methods=['PUT'])
@jwt_required()
def update_station(station_id):
    user = check_permission('environment.write')
    station = MonitoringStation.query.get(station_id)
    if not station:
        raise NotFoundError('Monitoring station not found')

    try:
        data = monitoring_station_schema.load(request.get_json() or {}, partial=True)
    except ValidationError as err:
        raise AppValidationError('Validation failed', details=err.messages)

    if 'station_id' in data and data['station_id'] != station.station_id:
        if MonitoringStation.query.filter_by(station_id=data['station_id']).first():
            raise AppValidationError('Station ID already exists')
        station.station_id = data['station_id']

    for key, value in data.items():
        if key != 'station_id' and hasattr(station, key):
            setattr(station, key, value)

    station.updated_at = datetime.utcnow()
    db.session.commit()

    return success_response(station.to_dict(), 'Monitoring station updated successfully')


@environment_bp.route('/<int:station_id>', methods=['DELETE'])
@jwt_required()
def delete_station(station_id):
    user = check_permission('environment.delete')
    station = MonitoringStation.query.get(station_id)
    if not station:
        raise NotFoundError('Monitoring station not found')

    db.session.delete(station)
    db.session.commit()
    return success_response(None, 'Monitoring station deleted successfully')


@environment_bp.route('/air-quality', methods=['GET'])
@jwt_required()
def list_air_quality_readings():
    check_permission('environment.read')

    query = AirQualityReading.query

    if request.args.get('station_id'):
        query = query.filter(AirQualityReading.station_id == request.args['station_id'])

    recorded_after = request.args.get('recorded_after')
    if recorded_after:
        try:
            query = query.filter(AirQualityReading.recorded_at >= datetime.fromisoformat(recorded_after))
        except ValueError:
            raise AppValidationError('Invalid recorded_after date')

    recorded_before = request.args.get('recorded_before')
    if recorded_before:
        try:
            query = query.filter(AirQualityReading.recorded_at <= datetime.fromisoformat(recorded_before))
        except ValueError:
            raise AppValidationError('Invalid recorded_before date')

    sort_by = request.args.get('sort_by', 'recorded_at')
    sort_order = request.args.get('sort_order', 'desc')
    sort_column = getattr(AirQualityReading, sort_by, AirQualityReading.recorded_at)
    if sort_order == 'desc':
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(asc(sort_column))

    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 50, type=int), 200)

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return success_response({
        'items': [r.to_dict() for r in pagination.items],
        'total': pagination.total,
        'page': pagination.page,
        'per_page': pagination.per_page,
        'pages': pagination.pages,
        'has_next': pagination.has_next,
        'has_prev': pagination.has_prev
    })


@environment_bp.route('/water-quality', methods=['GET'])
@jwt_required()
def list_water_quality_readings():
    check_permission('environment.read')

    query = WaterQualityReading.query

    if request.args.get('station_id'):
        query = query.filter(WaterQualityReading.station_id == request.args['station_id'])

    recorded_after = request.args.get('recorded_after')
    if recorded_after:
        try:
            query = query.filter(WaterQualityReading.recorded_at >= datetime.fromisoformat(recorded_after))
        except ValueError:
            raise AppValidationError('Invalid recorded_after date')

    recorded_before = request.args.get('recorded_before')
    if recorded_before:
        try:
            query = query.filter(WaterQualityReading.recorded_at <= datetime.fromisoformat(recorded_before))
        except ValueError:
            raise AppValidationError('Invalid recorded_before date')

    sort_by = request.args.get('sort_by', 'recorded_at')
    sort_order = request.args.get('sort_order', 'desc')
    sort_column = getattr(WaterQualityReading, sort_by, WaterQualityReading.recorded_at)
    if sort_order == 'desc':
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(asc(sort_column))

    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 50, type=int), 200)

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return success_response({
        'items': [r.to_dict() for r in pagination.items],
        'total': pagination.total,
        'page': pagination.page,
        'per_page': pagination.per_page,
        'pages': pagination.pages,
        'has_next': pagination.has_next,
        'has_prev': pagination.has_prev
    })


@environment_bp.route('/noise', methods=['GET'])
@jwt_required()
def list_noise_readings():
    check_permission('environment.read')

    query = NoiseReading.query

    if request.args.get('station_id'):
        query = query.filter(NoiseReading.station_id == request.args['station_id'])

    recorded_after = request.args.get('recorded_after')
    if recorded_after:
        try:
            query = query.filter(NoiseReading.recorded_at >= datetime.fromisoformat(recorded_after))
        except ValueError:
            raise AppValidationError('Invalid recorded_after date')

    recorded_before = request.args.get('recorded_before')
    if recorded_before:
        try:
            query = query.filter(NoiseReading.recorded_at <= datetime.fromisoformat(recorded_before))
        except ValueError:
            raise AppValidationError('Invalid recorded_before date')

    sort_by = request.args.get('sort_by', 'recorded_at')
    sort_order = request.args.get('sort_order', 'desc')
    sort_column = getattr(NoiseReading, sort_by, NoiseReading.recorded_at)
    if sort_order == 'desc':
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(asc(sort_column))

    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 50, type=int), 200)

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return success_response({
        'items': [r.to_dict() for r in pagination.items],
        'total': pagination.total,
        'page': pagination.page,
        'per_page': pagination.per_page,
        'pages': pagination.pages,
        'has_next': pagination.has_next,
        'has_prev': pagination.has_prev
    })


@environment_bp.route('/weather', methods=['GET'])
@jwt_required()
def list_weather_readings():
    check_permission('environment.read')

    query = WeatherReading.query

    if request.args.get('station_id'):
        query = query.filter(WeatherReading.station_id == request.args['station_id'])

    recorded_after = request.args.get('recorded_after')
    if recorded_after:
        try:
            query = query.filter(WeatherReading.recorded_at >= datetime.fromisoformat(recorded_after))
        except ValueError:
            raise AppValidationError('Invalid recorded_after date')

    recorded_before = request.args.get('recorded_before')
    if recorded_before:
        try:
            query = query.filter(WeatherReading.recorded_at <= datetime.fromisoformat(recorded_before))
        except ValueError:
            raise AppValidationError('Invalid recorded_before date')

    sort_by = request.args.get('sort_by', 'recorded_at')
    sort_order = request.args.get('sort_order', 'desc')
    sort_column = getattr(WeatherReading, sort_by, WeatherReading.recorded_at)
    if sort_order == 'desc':
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(asc(sort_column))

    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 50, type=int), 200)

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return success_response({
        'items': [r.to_dict() for r in pagination.items],
        'total': pagination.total,
        'page': pagination.page,
        'per_page': pagination.per_page,
        'pages': pagination.pages,
        'has_next': pagination.has_next,
        'has_prev': pagination.has_prev
    })


@environment_bp.route('/alerts', methods=['GET'])
@jwt_required()
def list_environmental_alerts():
    check_permission('environment.read')

    query = EnvironmentalAlert.query

    if request.args.get('station_id'):
        query = query.filter(EnvironmentalAlert.station_id == request.args['station_id'])
    if request.args.get('status'):
        query = query.filter(EnvironmentalAlert.status.ilike(f"%{request.args['status']}%"))
    if request.args.get('severity'):
        query = query.filter(EnvironmentalAlert.severity.ilike(f"%{request.args['severity']}%"))
    if request.args.get('parameter'):
        query = query.filter(EnvironmentalAlert.parameter.ilike(f"%{request.args['parameter']}%"))

    sort_by = request.args.get('sort_by', 'triggered_at')
    sort_order = request.args.get('sort_order', 'desc')
    sort_column = getattr(EnvironmentalAlert, sort_by, EnvironmentalAlert.triggered_at)
    if sort_order == 'desc':
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(asc(sort_column))

    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 50, type=int), 100)

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
