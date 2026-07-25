from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app.extensions import db
from app.models import (
    User, Container, ContainerStatus, ContainerType, ContainerHistory,
    Ship, Truck
)
from app.utils.exceptions import AuthorizationError, NotFoundError, ValidationError as AppValidationError
from app.utils.helpers import success_response, paginate_query
from sqlalchemy import func, or_, and_, desc
from datetime import datetime, timedelta
from marshmallow import Schema, fields, validate, ValidationError


containers_bp = Blueprint('containers', __name__, url_prefix='/api/v1/containers')


class ContainerSchema(Schema):
    container_id = fields.Str(required=True, validate=validate.Length(max=50))
    iso_code = fields.Str(validate=validate.Length(max=10))
    container_type = fields.Str(required=True, validate=validate.OneOf([t.value for t in ContainerType]))
    status = fields.Str(validate=validate.OneOf([s.value for s in ContainerStatus]))
    weight = fields.Float()
    max_weight = fields.Float()
    owner = fields.Str(validate=validate.Length(max=255))
    owner_code = fields.Str(validate=validate.Length(max=10))
    ship_id = fields.Int()
    truck_id = fields.Int()
    origin_port = fields.Str(validate=validate.Length(max=100))
    destination_port = fields.Str(validate=validate.Length(max=100))
    current_location = fields.Str(validate=validate.Length(max=255))
    bay = fields.Str(validate=validate.Length(max=20))
    row = fields.Str(validate=validate.Length(max=20))
    tier = fields.Str(validate=validate.Length(max=20))
    seal_number = fields.Str(validate=validate.Length(max=50))
    seal_status = fields.Str(validate=validate.Length(max=20))
    temperature = fields.Float()
    humidity = fields.Float()
    is_reefer = fields.Bool()
    is_hazardous = fields.Bool()
    hazardous_class = fields.Str(validate=validate.Length(max=10))
    un_number = fields.Str(validate=validate.Length(max=20))
    customs_status = fields.Str(validate=validate.Length(max=50))


container_schema = ContainerSchema()
containers_schema = ContainerSchema(many=True)


def check_permission(permission):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user or not user.has_permission(permission):
        raise AuthorizationError(f'Permission required: {permission}')
    return user


@containers_bp.route('', methods=['GET'])
@jwt_required()
def list_containers():
    check_permission('containers.read')
    
    query = Container.query
    
    # Search
    search = request.args.get('search', '').strip()
    if search:
        query = query.filter(or_(
            Container.container_id.ilike(f'%{search}%'),
            Container.iso_code.ilike(f'%{search}%'),
            Container.owner.ilike(f'%{search}%'),
            Container.current_location.ilike(f'%{search}%')
        ))
    
    # Filters
    if request.args.get('status'):
        query = query.filter(Container.status == ContainerStatus(request.args['status']))
    if request.args.get('container_type'):
        query = query.filter(Container.container_type == ContainerType(request.args['container_type']))
    if request.args.get('owner'):
        query = query.filter(Container.owner.ilike(f"%{request.args['owner']}%"))
    if request.args.get('destination_port'):
        query = query.filter(Container.destination_port.ilike(f"%{request.args['destination_port']}%"))
    if request.args.get('ship_id'):
        query = query.filter(Container.ship_id == request.args['ship_id'])
    if request.args.get('truck_id'):
        query = query.filter(Container.truck_id == request.args['truck_id'])
    if request.args.get('is_reefer') is not None:
        query = query.filter(Container.is_reefer == (request.args['is_reefer'].lower() == 'true'))
    if request.args.get('is_hazardous') is not None:
        query = query.filter(Container.is_hazardous == (request.args['is_hazardous'].lower() == 'true'))
    if request.args.get('current_location'):
        query = query.filter(Container.current_location.ilike(f"%{request.args['current_location']}%"))
    
    # Date range filters
    if request.args.get('loaded_after'):
        query = query.filter(Container.loaded_at >= datetime.fromisoformat(request.args['loaded_after']))
    if request.args.get('loaded_before'):
        query = query.filter(Container.loaded_at <= datetime.fromisoformat(request.args['loaded_before']))
    if request.args.get('gate_in_after'):
        query = query.filter(Container.gate_in_at >= datetime.fromisoformat(request.args['gate_in_after']))
    if request.args.get('gate_out_before'):
        query = query.filter(Container.gate_out_at <= datetime.fromisoformat(request.args['gate_out_before']))
    
    # Sorting
    sort_by = request.args.get('sort_by', 'created_at')
    sort_order = request.args.get('sort_order', 'desc')
    sort_column = getattr(Container, sort_by, Container.created_at)
    query = query.order_by(sort_column.desc() if sort_order == 'desc' else sort_column.asc())
    
    # Pagination
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


@containers_bp.route('/<int:container_id>', methods=['GET'])
@jwt_required()
def get_container(container_id):
    check_permission('containers.read')
    container = Container.query.get(container_id)
    if not container:
        raise NotFoundError('Container not found')
    return success_response(container.to_dict())


@containers_bp.route('', methods=['POST'])
@jwt_required()
def create_container():
    user = check_permission('containers.write')
    
    try:
        data = container_schema.load(request.get_json() or {})
    except ValidationError as err:
        raise AppValidationError('Validation failed', details=err.messages)
    
    if Container.query.filter_by(container_id=data['container_id']).first():
        raise AppValidationError('Container ID already exists')
    
    if data.get('ship_id'):
        ship = Ship.query.get(data['ship_id'])
        if not ship:
            raise NotFoundError('Ship not found')
    
    if data.get('truck_id'):
        truck = Truck.query.get(data['truck_id'])
        if not truck:
            raise NotFoundError('Truck not found')
    
    container = Container(**data)
    db.session.add(container)
    db.session.flush()
    
    # Add history entry
    history = ContainerHistory(
        container_id=container.id,
        event_type='CREATED',
        location=data.get('current_location'),
        description=f'Container {container.container_id} created',
        performed_by=user.get_full_name(),
        metadata={'created_by': user.id}
    )
    db.session.add(history)
    db.session.commit()
    
    return success_response(container.to_dict(), 'Container created successfully', 201)


@containers_bp.route('/<int:container_id>', methods=['PUT'])
@jwt_required()
def update_container(container_id):
    user = check_permission('containers.write')
    container = Container.query.get(container_id)
    if not container:
        raise NotFoundError('Container not found')
    
    try:
        data = container_schema.load(request.get_json() or {}, partial=True)
    except ValidationError as err:
        raise AppValidationError('Validation failed', details=err.messages)
    
    old_values = container.to_dict()
    
    if 'container_id' in data and data['container_id'] != container.container_id:
        if Container.query.filter_by(container_id=data['container_id']).first():
            raise AppValidationError('Container ID already exists')
        container.container_id = data['container_id']
    
    if 'ship_id' in data:
        if data['ship_id']:
            ship = Ship.query.get(data['ship_id'])
            if not ship:
                raise NotFoundError('Ship not found')
        container.ship_id = data['ship_id']
    
    if 'truck_id' in data:
        if data['truck_id']:
            truck = Truck.query.get(data['truck_id'])
            if not truck:
                raise NotFoundError('Truck not found')
        container.truck_id = data['truck_id']
    
    # Track status changes
    if 'status' in data and data['status'] != container.status.value:
        old_status = container.status.value
        container.status = ContainerStatus(data['status'])
        history = ContainerHistory(
            container_id=container.id,
            event_type='STATUS_CHANGE',
            location=container.current_location,
            description=f'Status changed from {old_status} to {container.status.value}',
            performed_by=user.get_full_name(),
            metadata={'old_status': old_status, 'new_status': container.status.value}
        )
        db.session.add(history)
        
        # Update timestamps based on status
        now = datetime.utcnow()
        if container.status == ContainerStatus.LOADED and not container.loaded_at:
            container.loaded_at = now
        elif container.status == ContainerStatus.IN_TRANSIT and not container.gate_out_at:
            container.gate_out_at = now
        elif container.status == ContainerStatus.DELIVERED and not container.gate_out_at:
            container.gate_out_at = now
    
    if 'current_location' in data and data['current_location'] != container.current_location:
        history = ContainerHistory(
            container_id=container.id,
            event_type='LOCATION_CHANGE',
            location=data['current_location'],
            description=f'Location changed to {data["current_location"]}',
            performed_by=user.get_full_name(),
            metadata={'old_location': container.current_location, 'new_location': data['current_location']}
        )
        db.session.add(history)
    
    for key, value in data.items():
        if key not in ['container_id', 'ship_id', 'truck_id', 'status', 'current_location'] and hasattr(container, key):
            setattr(container, key, value)
    
    container.updated_at = datetime.utcnow()
    db.session.commit()
    
    return success_response(container.to_dict(), 'Container updated successfully')


@containers_bp.route('/<int:container_id>', methods=['DELETE'])
@jwt_required()
def delete_container(container_id):
    user = check_permission('containers.delete')
    container = Container.query.get(container_id)
    if not container:
        raise NotFoundError('Container not found')
    
    db.session.delete(container)
    db.session.commit()
    return success_response(None, 'Container deleted successfully')


@containers_bp.route('/<int:container_id>/history', methods=['GET'])
@jwt_required()
def get_container_history(container_id):
    check_permission('containers.read')
    container = Container.query.get(container_id)
    if not container:
        raise NotFoundError('Container not found')
    
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 50, type=int), 100)
    
    history = ContainerHistory.query.filter_by(container_id=container_id)\
        .order_by(desc(ContainerHistory.created_at))\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    return success_response({
        'items': [h.to_dict() for h in history.items],
        'total': history.total,
        'page': history.page,
        'per_page': history.per_page,
        'pages': history.pages
    })


@containers_bp.route('/<int:container_id>/move', methods=['POST'])
@jwt_required()
def move_container(container_id):
    user = check_permission('containers.write')
    container = Container.query.get(container_id)
    if not container:
        raise NotFoundError('Container not found')
    
    data = request.get_json() or {}
    new_location = data.get('location')
    new_bay = data.get('bay')
    new_row = data.get('row')
    new_tier = data.get('tier')
    
    if not new_location and not any([new_bay, new_row, new_tier]):
        raise AppValidationError('Location or bay/row/tier required')
    
    old_location = container.current_location
    old_bay, old_row, old_tier = container.bay, container.row, container.tier
    
    if new_location:
        container.current_location = new_location
    if new_bay:
        container.bay = new_bay
    if new_row:
        container.row = new_row
    if new_tier:
        container.tier = new_tier
    
    history = ContainerHistory(
        container_id=container.id,
        event_type='MOVED',
        location=new_location or container.current_location,
        description=f'Container moved from {old_location} to {new_location or container.current_location}',
        performed_by=user.get_full_name(),
        metadata={
            'old_location': old_location,
            'new_location': new_location,
            'old_position': {'bay': old_bay, 'row': old_row, 'tier': old_tier},
            'new_position': {'bay': new_bay, 'row': new_row, 'tier': new_tier}
        }
    )
    db.session.add(history)
    
    container.updated_at = datetime.utcnow()
    db.session.commit()
    
    return success_response(container.to_dict(), 'Container moved successfully')


@containers_bp.route('/<int:container_id>/assign-ship', methods=['POST'])
@jwt_required()
def assign_to_ship(container_id):
    user = check_permission('containers.write')
    container = Container.query.get(container_id)
    if not container:
        raise NotFoundError('Container not found')
    
    data = request.get_json() or {}
    ship_id = data.get('ship_id')
    
    if ship_id:
        ship = Ship.query.get(ship_id)
        if not ship:
            raise NotFoundError('Ship not found')
        container.ship_id = ship_id
        container.status = ContainerStatus.LOADED
        if not container.loaded_at:
            container.loaded_at = datetime.utcnow()
    else:
        container.ship_id = None
        if container.status == ContainerStatus.LOADED:
            container.status = ContainerStatus.EMPTY
    
    history = ContainerHistory(
        container_id=container.id,
        event_type='SHIP_ASSIGNMENT',
        location=container.current_location,
        description=f'Container assigned to ship' if ship_id else 'Container unassigned from ship',
        performed_by=user.get_full_name(),
        metadata={'ship_id': ship_id}
    )
    db.session.add(history)
    
    container.updated_at = datetime.utcnow()
    db.session.commit()
    
    return success_response(container.to_dict(), 'Ship assignment updated')


@containers_bp.route('/<int:container_id>/assign-truck', methods=['POST'])
@jwt_required()
def assign_to_truck(container_id):
    user = check_permission('containers.write')
    container = Container.query.get(container_id)
    if not container:
        raise NotFoundError('Container not found')
    
    data = request.get_json() or {}
    truck_id = data.get('truck_id')
    
    if truck_id:
        truck = Truck.query.get(truck_id)
        if not truck:
            raise NotFoundError('Truck not found')
        if truck.assigned_container_id and truck.assigned_container_id != container_id:
            raise AppValidationError('Truck already assigned to another container')
        container.truck_id = truck_id
        truck.assigned_container_id = container_id
        container.status = ContainerStatus.IN_TRANSIT
        if not container.gate_out_at:
            container.gate_out_at = datetime.utcnow()
    else:
        if container.truck_id:
            old_truck = Truck.query.get(container.truck_id)
            if old_truck:
                old_truck.assigned_container_id = None
        container.truck_id = None
        if container.status == ContainerStatus.IN_TRANSIT:
            container.status = ContainerStatus.LOADED
    
    history = ContainerHistory(
        container_id=container.id,
        event_type='TRUCK_ASSIGNMENT',
        location=container.current_location,
        description=f'Container assigned to truck' if truck_id else 'Container unassigned from truck',
        performed_by=user.get_full_name(),
        metadata={'truck_id': truck_id}
    )
    db.session.add(history)
    
    container.updated_at = datetime.utcnow()
    db.session.commit()
    
    return success_response(container.to_dict(), 'Truck assignment updated')


@containers_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_container_stats():
    check_permission('containers.read')
    
    total = Container.query.count()
    by_status = db.session.query(Container.status, func.count(Container.id)).group_by(Container.status).all()
    by_type = db.session.query(Container.container_type, func.count(Container.id)).group_by(Container.container_type).all()
    by_owner = db.session.query(Container.owner, func.count(Container.id)).filter(Container.owner.isnot(None)).group_by(Container.owner).order_by(desc(func.count(Container.id))).limit(10).all()
    
    in_transit = Container.query.filter(Container.status == ContainerStatus.IN_TRANSIT).count()
    at_port = Container.query.filter(Container.status.in_([ContainerStatus.LOADED, ContainerStatus.EMPTY])).count()
    customs_hold = Container.query.filter(Container.customs_status == 'HOLD').count()
    
    return success_response({
        'total': total,
        'by_status': {s.value: c for s, c in by_status},
        'by_type': {t.value: c for t, c in by_type},
        'top_owners': [{'owner': o, 'count': c} for o, c in by_owner],
        'in_transit': in_transit,
        'at_port': at_port,
        'customs_hold': customs_hold
    })


@containers_bp.route('/type-distribution', methods=['GET'])
@jwt_required()
def get_type_distribution():
    check_permission('containers.read')
    
    data = db.session.query(Container.container_type, func.count(Container.id)).group_by(Container.container_type).all()
    
    labels = [t.value for t, _ in data]
    values = [c for _, c in data]
    
    colors = {
        '20ft': 'rgba(54, 162, 235, 0.8)',
        '40ft': 'rgba(75, 192, 192, 0.8)',
        '40ft HC': 'rgba(255, 206, 86, 0.8)',
        'Reefer': 'rgba(255, 99, 132, 0.8)',
        'Hazmat': 'rgba(153, 102, 255, 0.8)',
        'Tank': 'rgba(255, 159, 64, 0.8)',
        'Open Top': 'rgba(199, 199, 199, 0.8)',
        'Flat Rack': 'rgba(83, 102, 255, 0.8)'
    }
    
    return success_response({
        'labels': labels,
        'datasets': [{
            'label': 'Containers by Type',
            'data': values,
            'backgroundColor': [colors.get(l, 'rgba(108, 117, 125, 0.8)') for l in labels],
            'borderColor': [colors.get(l, 'rgba(108, 117, 125, 1)').replace('0.8', '1') for l in labels],
            'borderWidth': 2
        }]
    })


@containers_bp.route('/flow-chart', methods=['GET'])
@jwt_required()
def get_flow_chart():
    check_permission('containers.read')
    
    period = request.args.get('period', 'monthly')
    months = int(request.args.get('months', 12))
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=months * 30)
    
    # Inbound (loaded at port)
    inbound = db.session.query(
        func.date_trunc('month', Container.loaded_at).label('month'),
        func.count(Container.id).label('count')
    ).filter(
        Container.loaded_at >= start_date,
        Container.loaded_at.isnot(None)
    ).group_by(func.date_trunc('month', Container.loaded_at)).all()
    
    # Outbound (gate out)
    outbound = db.session.query(
        func.date_trunc('month', Container.gate_out_at).label('month'),
        func.count(Container.id).label('count')
    ).filter(
        Container.gate_out_at >= start_date,
        Container.gate_out_at.isnot(None)
    ).group_by(func.date_trunc('month', Container.gate_out_at)).all()
    
    # Transferred (moved between locations)
    transferred = db.session.query(
        func.date_trunc('month', ContainerHistory.created_at).label('month'),
        func.count(ContainerHistory.id).label('count')
    ).filter(
        ContainerHistory.created_at >= start_date,
        ContainerHistory.event_type == 'MOVED'
    ).group_by(func.date_trunc('month', ContainerHistory.created_at)).all()
    
    labels = []
    current = start_date.replace(day=1)
    while current <= end_date:
        labels.append(current.strftime('%b %Y'))
        if current.month == 12:
            current = current.replace(year=current.year + 1, month=1)
        else:
            current = current.replace(month=current.month + 1)
    
    inbound_data = [0] * len(labels)
    outbound_data = [0] * len(labels)
    transferred_data = [0] * len(labels)
    
    for i, label in enumerate(labels):
        for m, c in inbound:
            if m and m.strftime('%b %Y') == label:
                inbound_data[i] = c
        for m, c in outbound:
            if m and m.strftime('%b %Y') == label:
                outbound_data[i] = c
        for m, c in transferred:
            if m and m.strftime('%b %Y') == label:
                transferred_data[i] = c
    
    return success_response({
        'labels': labels,
        'datasets': [
            {'label': 'Inbound', 'data': inbound_data, 'backgroundColor': 'rgba(54, 162, 235, 0.8)', 'borderColor': 'rgba(54, 162, 235, 1)', 'borderWidth': 1, 'borderRadius': 4},
            {'label': 'Outbound', 'data': outbound_data, 'backgroundColor': 'rgba(75, 192, 192, 0.8)', 'borderColor': 'rgba(75, 192, 192, 1)', 'borderWidth': 1, 'borderRadius': 4},
            {'label': 'Transferred', 'data': transferred_data, 'backgroundColor': 'rgba(255, 206, 86, 0.8)', 'borderColor': 'rgba(255, 206, 86, 1)', 'borderWidth': 1, 'borderRadius': 4}
        ]
    })