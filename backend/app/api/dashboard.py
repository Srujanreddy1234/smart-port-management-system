from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app.extensions import db
from app.models import (
    User, Ship, ShipStatus, Container, ContainerStatus,
    Truck, TruckStatus, SecurityIncident, IncidentStatus, IncidentSeverity,
    Equipment, EquipmentStatus, MaintenanceStatus, MaintenanceType,
    AirQualityReading, WaterQualityReading, NoiseReading, WeatherReading,
    Report, ReportStatus
)
from app.utils.exceptions import AuthorizationError
from app.utils.helpers import success_response, paginate_query
from sqlalchemy import func, and_, or_, desc
from datetime import datetime, timedelta


dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/api/v1/dashboard')


def require_permission(permission):
    def decorator(fn):
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            user_id = get_jwt_identity()
            user = User.query.get(user_id)
            if not user or not user.has_permission(permission):
                raise AuthorizationError(f'Permission required: {permission}')
            return fn(*args, **kwargs)
        wrapper.__name__ = fn.__name__
        return wrapper
    return decorator


@dashboard_bp.route('/kpis', methods=['GET'])
@jwt_required()
def get_kpis():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        raise AuthorizationError('User not found')

    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)

    total_ships = Ship.query.count()
    ships_docked = Ship.query.filter(Ship.status == ShipStatus.AT_BERTH).count()
    ships_waiting = Ship.query.filter(Ship.status.in_([ShipStatus.ANCHORED, ShipStatus.APPROACHING, ShipStatus.IN_CHANNEL])).count()

    total_containers = Container.query.count()
    containers_loaded = Container.query.filter(Container.status == ContainerStatus.LOADED).count()
    containers_in_transit = Container.query.filter(Container.status == ContainerStatus.IN_TRANSIT).count()

    total_trucks = Truck.query.count()
    trucks_in_transit = Truck.query.filter(Truck.status == TruckStatus.IN_TRANSIT).count()
    trucks_loading = Truck.query.filter(Truck.status == TruckStatus.LOADING).count()

    active_alerts = SecurityIncident.query.filter(SecurityIncident.status == IncidentStatus.ACTIVE).count()
    critical_alerts = SecurityIncident.query.filter(
        SecurityIncident.severity == IncidentSeverity.CRITICAL,
        SecurityIncident.status == IncidentStatus.ACTIVE
    ).count()

    operational_equipment = Equipment.query.filter(Equipment.status == EquipmentStatus.OPERATIONAL).count()
    maintenance_equipment = Equipment.query.filter(Equipment.status == EquipmentStatus.MAINTENANCE).count()
    total_equipment = Equipment.query.count()

    latest_aqi = AirQualityReading.query.order_by(desc(AirQualityReading.recorded_at)).first()
    aqi_value = latest_aqi.aqi if latest_aqi else 42
    aqi_category = latest_aqi.aqi_category if latest_aqi else 'Good'

    latest_noise = NoiseReading.query.order_by(desc(NoiseReading.recorded_at)).first()
    noise_value = round(latest_noise.leq, 1) if latest_noise else 68

    latest_weather = WeatherReading.query.order_by(desc(WeatherReading.recorded_at)).first()
    weather = {
        'temperature': latest_weather.temperature if latest_weather else 32,
        'humidity': latest_weather.humidity if latest_weather else 72,
        'wind_speed': latest_weather.wind_speed if latest_weather else 18,
        'condition': latest_weather.weather_condition if latest_weather else 'Partly Cloudy'
    }

    revenue_this_month = 248000000
    revenue_last_month = 221000000
    revenue_growth = ((revenue_this_month - revenue_last_month) / revenue_last_month) * 100

    throughput_this_month = 15847
    throughput_last_month = 14673
    throughput_growth = ((throughput_this_month - throughput_last_month) / throughput_last_month) * 100

    kpis = {
        'total_ships': {
            'value': total_ships,
            'label': 'Total Ships',
            'change': 12,
            'change_label': 'from last week',
            'icon': 'fa-ship',
            'color': 'primary'
        },
        'ships_docked': {
            'value': ships_docked,
            'label': 'Ships Docked',
            'change': 2,
            'change_label': 'unloading',
            'icon': 'fa-anchor',
            'color': 'success'
        },
        'ships_waiting': {
            'value': ships_waiting,
            'label': 'Ships Waiting',
            'change': -1,
            'change_label': 'awaiting berth',
            'icon': 'fa-clock',
            'color': 'warning'
        },
        'total_containers': {
            'value': total_containers,
            'label': 'Containers',
            'change': 8,
            'change_label': 'from last week',
            'icon': 'fa-boxes-stacked',
            'color': 'info'
        },
        'containers_loaded': {
            'value': containers_loaded,
            'label': 'Loaded',
            'change': 5,
            'change_label': 'ready for dispatch',
            'icon': 'fa-box',
            'color': 'success'
        },
        'containers_in_transit': {
            'value': containers_in_transit,
            'label': 'In Transit',
            'change': 15,
            'change_label': 'out for delivery',
            'icon': 'fa-truck-fast',
            'color': 'warning'
        },
        'total_trucks': {
            'value': total_trucks,
            'label': 'Total Trucks',
            'change': 7,
            'change_label': 'from last week',
            'icon': 'fa-truck',
            'color': 'primary'
        },
        'trucks_in_transit': {
            'value': trucks_in_transit,
            'label': 'In Transit',
            'change': 12,
            'change_label': 'on the road',
            'icon': 'fa-truck-moving',
            'color': 'info'
        },
        'trucks_loading': {
            'value': trucks_loading,
            'label': 'Loading',
            'change': -3,
            'change_label': 'at berths',
            'icon': 'fa-truck-loading',
            'color': 'warning'
        },
        'active_alerts': {
            'value': active_alerts,
            'label': 'Active Alerts',
            'change': 2,
            'change_label': 'new today',
            'icon': 'fa-shield-halved',
            'color': 'danger'
        },
        'critical_alerts': {
            'value': critical_alerts,
            'label': 'Critical Alerts',
            'change': 0,
            'change_label': 'requiring attention',
            'icon': 'fa-exclamation-triangle',
            'color': 'danger'
        },
        'operational_equipment': {
            'value': operational_equipment,
            'label': 'Equipment Operational',
            'change': 5,
            'change_label': 'of total',
            'icon': 'fa-cogs',
            'color': 'success'
        },
        'maintenance_equipment': {
            'value': maintenance_equipment,
            'label': 'Under Maintenance',
            'change': 2,
            'change_label': 'scheduled',
            'icon': 'fa-tools',
            'color': 'warning'
        },
        'total_equipment': {
            'value': total_equipment,
            'label': 'Total Equipment',
            'change': 3,
            'change_label': 'new this month',
            'icon': 'fa-wrench',
            'color': 'primary'
        },
        'aqi': {
            'value': aqi_value,
            'label': 'Air Quality Index',
            'category': aqi_category,
            'icon': 'fa-wind',
            'color': 'success' if aqi_value <= 50 else 'warning' if aqi_value <= 100 else 'danger'
        },
        'noise_level': {
            'value': noise_value,
            'label': 'Noise Level',
            'unit': 'dB',
            'icon': 'fa-volume-high',
            'color': 'success' if noise_value <= 70 else 'warning' if noise_value <= 85 else 'danger'
        },
        'weather': weather,
        'revenue': {
            'value': revenue_this_month,
            'label': 'Revenue (Monthly)',
            'currency': 'INR',
            'change': round(revenue_growth, 1),
            'change_label': 'from last month',
            'icon': 'fa-indian-rupee-sign',
            'color': 'success' if revenue_growth > 0 else 'danger'
        },
        'throughput': {
            'value': throughput_this_month,
            'label': 'Container Throughput',
            'unit': 'TEU',
            'change': round(throughput_growth, 1),
            'change_label': 'from last month',
            'icon': 'fa-gauge-high',
            'color': 'success' if throughput_growth > 0 else 'danger'
        }
    }

    return success_response(kpis)


@dashboard_bp.route('/charts/throughput', methods=['GET'])
@jwt_required()
def get_throughput_chart():
    days = int(request.args.get('days', 30))
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    daily_data = db.session.query(
        func.date(Container.created_at).label('date'),
        func.count(Container.id).label('count')
    ).filter(
        Container.created_at >= start_date,
        Container.status.in_([ContainerStatus.LOADED, ContainerStatus.DELIVERED])
    ).group_by(func.date(Container.created_at)).all()

    labels = []
    data = []
    current = start_date
    while current <= end_date:
        labels.append(current.strftime('%b %d'))
        day_data = next((d for d in daily_data if d.date == current.date()), None)
        data.append(day_data.count if day_data else 0)
        current += timedelta(days=1)

    return success_response({
        'labels': labels,
        'datasets': [
            {
                'label': 'Containers Handled',
                'data': data,
                'borderColor': 'rgba(13, 110, 253, 1)',
                'backgroundColor': 'rgba(13, 110, 253, 0.1)',
                'fill': True,
                'tension': 0.4
            }
        ]
    })


@dashboard_bp.route('/charts/vessel-arrivals', methods=['GET'])
@jwt_required()
def get_vessel_arrivals_chart():
    days = int(request.args.get('days', 30))
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
            {
                'label': 'Arrivals',
                'data': arrival_data,
                'borderColor': 'rgba(13, 110, 253, 1)',
                'backgroundColor': 'rgba(13, 110, 253, 0.1)',
                'fill': True,
                'tension': 0.4
            },
            {
                'label': 'Departures',
                'data': departure_data,
                'borderColor': 'rgba(25, 135, 84, 1)',
                'backgroundColor': 'rgba(25, 135, 84, 0.1)',
                'fill': True,
                'tension': 0.4
            }
        ]
    })


@dashboard_bp.route('/charts/container-distribution', methods=['GET'])
@jwt_required()
def get_container_distribution():
    distribution = db.session.query(
        Container.container_type,
        func.count(Container.id)
    ).group_by(Container.container_type).all()

    type_labels = [d[0].value for d in distribution]
    type_data = [d[1] for d in distribution]

    status_distribution = db.session.query(
        Container.status,
        func.count(Container.id)
    ).group_by(Container.status).all()

    status_labels = [d[0].value for d in status_distribution]
    status_data = [d[1] for d in status_distribution]

    return success_response({
        'by_type': {
            'labels': type_labels,
            'data': type_data
        },
        'by_status': {
            'labels': status_labels,
            'data': status_data
        }
    })


@dashboard_bp.route('/charts/truck-traffic', methods=['GET'])
@jwt_required()
def get_truck_traffic_chart():
    hours = 24
    end_time = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
    start_time = end_time - timedelta(hours=hours)

    hourly_data = db.session.query(
        func.extract('hour', Truck.gate_in_time).label('hour'),
        func.count(Truck.id).label('count')
    ).filter(
        Truck.gate_in_time >= start_time,
        Truck.gate_in_time.isnot(None)
    ).group_by(func.extract('hour', Truck.gate_in_time)).all()

    labels = []
    data = []
    current = start_time
    while current <= end_time:
        labels.append(current.strftime('%H:00'))
        hour_data = next((d for d in hourly_data if int(d.hour) == current.hour), None)
        data.append(hour_data.count if hour_data else 0)
        current += timedelta(hours=1)

    return success_response({
        'labels': labels,
        'datasets': [{
            'label': 'Trucks',
            'data': data,
            'backgroundColor': 'rgba(255, 193, 7, 0.7)',
            'borderColor': 'rgba(255, 193, 7, 1)',
            'borderWidth': 1,
            'borderRadius': 6
        }]
    })


@dashboard_bp.route('/charts/equipment-health', methods=['GET'])
@jwt_required()
def get_equipment_health():
    health_ranges = [
        (90, 100, 'Excellent'),
        (70, 89, 'Good'),
        (50, 69, 'Fair'),
        (0, 49, 'Poor')
    ]

    labels = []
    data = []
    colors = ['#198754', '#0dcaf0', '#ffc107', '#dc3545']

    for min_h, max_h, label in health_ranges:
        count = Equipment.query.filter(
            Equipment.health_percentage >= min_h,
            Equipment.health_percentage <= max_h
        ).count()
        labels.append(label)
        data.append(count)

    return success_response({
        'labels': labels,
        'datasets': [{
            'data': data,
            'backgroundColor': colors,
            'borderWidth': 0,
            'hoverOffset': 8
        }]
    })


@dashboard_bp.route('/charts/environmental-trends', methods=['GET'])
@jwt_required()
def get_environmental_trends():
    parameter = request.args.get('parameter', 'aqi')
    hours = int(request.args.get('hours', 24))

    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=hours)

    if parameter == 'aqi':
        readings = AirQualityReading.query.filter(
            AirQualityReading.recorded_at >= start_time
        ).order_by(AirQualityReading.recorded_at).all()
        labels = [r.recorded_at.strftime('%H:%M') for r in readings]
        data = [r.aqi for r in readings]
        label = 'AQI'
    elif parameter == 'noise':
        readings = NoiseReading.query.filter(
            NoiseReading.recorded_at >= start_time
        ).order_by(NoiseReading.recorded_at).all()
        labels = [r.recorded_at.strftime('%H:%M') for r in readings]
        data = [r.leq for r in readings]
        label = 'Noise (dB)'
    elif parameter == 'temperature':
        readings = WeatherReading.query.filter(
            WeatherReading.recorded_at >= start_time
        ).order_by(WeatherReading.recorded_at).all()
        labels = [r.recorded_at.strftime('%H:%M') for r in readings]
        data = [r.temperature for r in readings]
        label = 'Temperature (°C)'
    else:
        readings = WaterQualityReading.query.filter(
            WaterQualityReading.recorded_at >= start_time
        ).order_by(WaterQualityReading.recorded_at).all()
        labels = [r.recorded_at.strftime('%H:%M') for r in readings]
        data = [r.ph for r in readings]
        label = 'Water pH'

    return success_response({
        'labels': labels,
        'datasets': [{
            'label': label,
            'data': data,
            'borderColor': 'rgba(13, 110, 253, 1)',
            'backgroundColor': 'rgba(13, 110, 253, 0.1)',
            'fill': True,
            'tension': 0.4
        }]
    })


@dashboard_bp.route('/vessel-status', methods=['GET'])
@jwt_required()
def get_vessel_status():
    status_counts = db.session.query(
        Ship.status,
        func.count(Ship.id)
    ).group_by(Ship.status).all()

    result = {}
    for status, count in status_counts:
        result[status.value] = count

    return success_response(result)


@dashboard_bp.route('/berth-occupancy', methods=['GET'])
@jwt_required()
def get_berth_occupancy():
    berths = ['Berth 1', 'Berth 2', 'Berth 3', 'Berth 4', 'Berth 5', 'Berth 6', 'Berth 7', 'Berth 8', 'Berth 9']
    
    occupancy = []
    for berth in berths:
        ship = Ship.query.filter(Ship.current_berth == berth, Ship.status == ShipStatus.AT_BERTH).first()
        occupancy.append({
            'berth': berth,
            'occupied': ship is not None,
            'ship': ship.name if ship else None,
            'ship_id': ship.ship_id if ship else None,
            'occupancy_pct': 94 if berth == 'Berth 3' else 87 if berth == 'Berth 1' else 72 if berth == 'Berth 7' else 58 if berth == 'Berth 5' else 35
        })

    return success_response(occupancy)


@dashboard_bp.route('/recent-activity', methods=['GET'])
@jwt_required()
def get_recent_activity():
    limit = int(request.args.get('limit', 10))
    
    activities = []

    recent_ships = Ship.query.filter(Ship.ata.isnot(None)).order_by(desc(Ship.ata)).limit(5).all()
    for ship in recent_ships:
        activities.append({
            'type': 'ship_arrival',
            'icon': 'fa-ship',
            'color': 'primary',
            'title': f'{ship.name} berthed at {ship.current_berth}',
            'description': 'Container discharge in progress',
            'timestamp': ship.ata.isoformat() if ship.ata else ship.created_at.isoformat()
        })

    recent_containers = Container.query.filter(Container.gate_out_at.isnot(None)).order_by(desc(Container.gate_out_at)).limit(3).all()
    for container in recent_containers:
        activities.append({
            'type': 'container_departure',
            'icon': 'fa-truck',
            'color': 'info',
            'title': f'Truck loaded with {container.container_id}',
            'description': f'Heading to {container.destination_port}',
            'timestamp': container.gate_out_at.isoformat() if container.gate_out_at else container.updated_at.isoformat()
        })

    recent_incidents = SecurityIncident.query.order_by(desc(SecurityIncident.detected_at)).limit(2).all()
    for incident in recent_incidents:
        activities.append({
            'type': 'security_alert',
            'icon': 'fa-exclamation',
            'color': 'danger',
            'title': f'{incident.incident_type.value} — {incident.zone.value}',
            'description': incident.description,
            'timestamp': incident.detected_at.isoformat()
        })

    activities.sort(key=lambda x: x['timestamp'], reverse=True)

    return success_response(activities[:limit])