from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import Schema, fields, validate, ValidationError
from app.extensions import db
from app.models import (
    Report, ReportType, ReportFormat, ReportStatus,
    Ship, Container, Truck, Equipment, User, Berth
)
from app.utils.exceptions import ValidationError as AppValidationError, NotFoundError, AuthorizationError
from app.utils.helpers import success_response
from sqlalchemy import func, desc
from datetime import datetime, timedelta
import csv
import io


reports_bp = Blueprint('reports', __name__, url_prefix='/api/v1/reports')


class ReportCreateSchema(Schema):
    title = fields.Str(required=True, validate=validate.Length(min=1, max=255))
    report_type = fields.Str(required=True, validate=validate.OneOf([r.value for r in ReportType]))
    description = fields.Str()
    format = fields.Str(validate=validate.OneOf([f.value for f in ReportFormat]))
    date_from = fields.DateTime()
    date_to = fields.DateTime()
    parameters = fields.Dict(keys=fields.Str(), values=fields.Raw())


@reports_bp.route('', methods=['GET'])
@jwt_required()
def list_reports():
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    if not current_user or not current_user.has_permission('reports.read'):
        raise AuthorizationError('Insufficient permissions')

    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)
    status = request.args.get('status')
    report_type = request.args.get('report_type')

    query = Report.query

    if status:
        try:
            query = query.filter(Report.status == ReportStatus(status))
        except ValueError:
            pass

    if report_type:
        try:
            query = query.filter(Report.report_type == ReportType(report_type))
        except ValueError:
            pass

    query = query.order_by(desc(Report.created_at))
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return success_response({
        'items': [r.to_dict() for r in pagination.items],
        'total': pagination.total,
        'page': pagination.page,
        'per_page': pagination.per_page,
        'pages': pagination.pages,
    })


@reports_bp.route('', methods=['POST'])
@jwt_required()
def create_report():
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    if not current_user or not current_user.has_permission('reports.write'):
        raise AuthorizationError('Insufficient permissions')

    try:
        data = ReportCreateSchema().load(request.get_json() or {})
    except ValidationError as err:
        return jsonify({'success': False, 'errors': err.messages}), 400

    report = Report(
        report_id=f'RPT-{datetime.utcnow().strftime("%Y%m%d%H%M%S")}',
        title=data['title'],
        report_type=ReportType(data['report_type']),
        description=data.get('description'),
        format=ReportFormat(data.get('format', 'PDF')),
        status=ReportStatus.PENDING,
        generated_by_id=current_user_id,
        parameters=data.get('parameters'),
        date_from=data.get('date_from'),
        date_to=data.get('date_to'),
    )
    db.session.add(report)
    db.session.commit()

    _generate_report(report)

    return success_response(report.to_dict(), 'Report created', 201)


@reports_bp.route('/<int:report_id>', methods=['GET'])
@jwt_required()
def get_report(report_id):
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    if not current_user or not current_user.has_permission('reports.read'):
        raise AuthorizationError('Insufficient permissions')

    report = Report.query.get(report_id)
    if not report:
        raise NotFoundError('Report not found')
    return success_response(report.to_dict())


@reports_bp.route('/<int:report_id>/download', methods=['GET'])
@jwt_required()
def download_report(report_id):
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    if not current_user or not current_user.has_permission('reports.read'):
        raise AuthorizationError('Insufficient permissions')

    report = Report.query.get(report_id)
    if not report:
        raise NotFoundError('Report not found')

    if report.status != ReportStatus.READY:
        raise AppValidationError('Report not ready for download')

    report.download_count += 1
    db.session.commit()

    return success_response({
        'report': report.to_dict(),
        'download_url': f'/api/v1/reports/{report_id}/file'
    })


@reports_bp.route('/<int:report_id>/file', methods=['GET'])
@jwt_required()
def download_report_file(report_id):
    report = Report.query.get(report_id)
    if not report:
        raise NotFoundError('Report not found')

    if report.format == ReportFormat.CSV:
        return _generate_csv(report)
    elif report.format == ReportFormat.JSON:
        return _generate_json(report)
    else:
        return success_response(report.to_dict())


@reports_bp.route('/ship-traffic', methods=['GET'])
@jwt_required()
def ship_traffic_report():
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    if not current_user or not current_user.has_permission('reports.read'):
        raise AuthorizationError('Insufficient permissions')

    days = request.args.get('days', 30, type=int)
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    total_ships = Ship.query.count()
    by_status = db.session.query(Ship.status, func.count(Ship.id)).group_by(Ship.status).all()
    by_type = db.session.query(Ship.vessel_type, func.count(Ship.id)).group_by(Ship.vessel_type).all()

    arrivals = db.session.query(func.count(Ship.id)).filter(
        Ship.ata >= start_date, Ship.ata.isnot(None)
    ).scalar() or 0
    departures = db.session.query(func.count(Ship.id)).filter(
        Ship.atd >= start_date, Ship.atd.isnot(None)
    ).scalar() or 0

    return success_response({
        'period': {'from': start_date.isoformat(), 'to': end_date.isoformat()},
        'total_ships': total_ships,
        'arrivals': arrivals,
        'departures': departures,
        'by_status': {s.value: c for s, c in by_status},
        'by_type': {t.value: c for t, c in by_type},
    })


@reports_bp.route('/container-throughput', methods=['GET'])
@jwt_required()
def container_throughput_report():
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    if not current_user or not current_user.has_permission('reports.read'):
        raise AuthorizationError('Insufficient permissions')

    days = request.args.get('days', 30, type=int)
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    total = Container.query.count()
    by_status = db.session.query(Container.status, func.count(Container.id)).group_by(Container.status).all()
    by_type = db.session.query(Container.container_type, func.count(Container.id)).group_by(Container.container_type).all()

    loaded = db.session.query(func.count(Container.id)).filter(
        Container.status == Container.status.value if hasattr(Container.status, 'value') else Container.status == 'Loaded'
    ).scalar() or 0

    return success_response({
        'period': {'from': start_date.isoformat(), 'to': end_date.isoformat()},
        'total_containers': total,
        'loaded': loaded,
        'by_status': {s.value: c for s, c in by_status} if by_status else {},
        'by_type': {t.value: c for t, c in by_type} if by_type else {},
    })


@reports_bp.route('/dashboard-summary', methods=['GET'])
@jwt_required()
def dashboard_summary():
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    if not current_user or not current_user.has_permission('reports.read'):
        raise AuthorizationError('Insufficient permissions')

    return success_response({
        'ships': {'total': Ship.query.count()},
        'containers': {'total': Container.query.count()},
        'trucks': {'total': Truck.query.count()},
        'berths': {'total': Berth.query.count()},
        'equipment': {'total': Equipment.query.count()},
        'users': {'total': User.query.count()},
    })


def _generate_report(report):
    report.status = ReportStatus.GENERATING
    report.started_at = datetime.utcnow()
    db.session.commit()

    try:
        data = {}
        if report.report_type == ReportType.VESSEL_TRAFFIC:
            data = _collect_ship_data(report)
        elif report.report_type == ReportType.CONTAINER_THROUGHPUT:
            data = _collect_container_data(report)
        elif report.report_type == ReportType.TRUCK_OPERATIONS:
            data = _collect_truck_data(report)
        elif report.report_type == ReportType.EQUIPMENT_PERFORMANCE:
            data = _collect_equipment_data(report)
        else:
            data = _collect_general_data(report)

        report.report_metadata = data
        report.status = ReportStatus.READY
        report.completed_at = datetime.utcnow()
        if not report.expires_at:
            report.expires_at = datetime.utcnow() + timedelta(days=30)
        db.session.commit()

    except Exception as e:
        report.status = ReportStatus.FAILED
        report.error_message = str(e)
        db.session.commit()


def _collect_ship_data(report):
    query = Ship.query
    if report.date_from:
        query = query.filter(Ship.created_at >= report.date_from)
    if report.date_to:
        query = query.filter(Ship.created_at <= report.date_to)
    ships = query.all()
    return {'ships': [s.to_dict() for s in ships], 'count': len(ships)}


def _collect_container_data(report):
    query = Container.query
    if report.date_from:
        query = query.filter(Container.created_at >= report.date_from)
    if report.date_to:
        query = query.filter(Container.created_at <= report.date_to)
    containers = query.all()
    return {'containers': [c.to_dict() for c in containers], 'count': len(containers)}


def _collect_truck_data(report):
    query = Truck.query
    trucks = query.all()
    return {'trucks': [t.to_dict() for t in trucks], 'count': len(trucks)}


def _collect_equipment_data(report):
    equipment = Equipment.query.all()
    return {'equipment': [e.to_dict() for e in equipment], 'count': len(equipment)}


def _collect_general_data(report):
    return {
        'ships': Ship.query.count(),
        'containers': Container.query.count(),
        'trucks': Truck.query.count(),
        'equipment': Equipment.query.count(),
    }


def _generate_csv(report):
    output = io.StringIO()
    writer = csv.writer(output)

    if report.report_metadata and 'ships' in report.report_metadata:
        writer.writerow(['Ship ID', 'Name', 'Type', 'Flag', 'Status', 'Berth', 'ETA', 'Agent'])
        for ship in report.report_metadata['ships']:
            writer.writerow([
                ship.get('ship_id'), ship.get('name'), ship.get('vessel_type'),
                ship.get('flag'), ship.get('status'), ship.get('current_berth'),
                ship.get('eta'), ship.get('agent')
            ])
    elif report.report_metadata and 'containers' in report.report_metadata:
        writer.writerow(['Container ID', 'Type', 'Status', 'Weight', 'Owner', 'Origin', 'Destination'])
        for c in report.report_metadata['containers']:
            writer.writerow([
                c.get('container_id'), c.get('container_type'), c.get('status'),
                c.get('weight'), c.get('owner'), c.get('origin_port'), c.get('destination_port')
            ])
    else:
        writer.writerow(['Metric', 'Value'])
        for key, value in (report.report_metadata or {}).items():
            writer.writerow([key, value])

    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode()),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'{report.report_id}.csv'
    )


def _generate_json(report):
    return success_response(report.report_metadata)