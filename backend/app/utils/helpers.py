from flask import request, jsonify
from sqlalchemy import or_, and_
from functools import wraps


def success_response(data=None, message=None, status_code=200):
    response = {'success': True}
    if data is not None:
        response['data'] = data
    if message:
        response['message'] = message
    return jsonify(response), status_code


def error_response(message, status_code=400, errors=None, details=None):
    response = {'success': False, 'message': message}
    if errors:
        response['errors'] = errors
    if details:
        response['details'] = details
    return jsonify(response), status_code


def paginate_query(query, page=1, per_page=20, max_per_page=100):
    page = max(1, int(page))
    per_page = min(max(1, int(per_page)), max_per_page)
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    return {
        'items': pagination.items,
        'total': pagination.total,
        'page': pagination.page,
        'per_page': pagination.per_page,
        'pages': pagination.pages,
        'has_next': pagination.has_next,
        'has_prev': pagination.has_prev,
    }


def apply_filters(query, model, filters, search_fields=None):
    for key, value in filters.items():
        if value is None or value == '':
            continue
        if hasattr(model, key):
            column = getattr(model, key)
            if isinstance(value, str) and value.startswith('%') and value.endswith('%'):
                query = query.filter(column.ilike(value))
            elif isinstance(value, str):
                query = query.filter(column.ilike(f'%{value}%'))
            else:
                query = query.filter(column == value)
    return query


def get_sort_params(default_sort='created_at', default_order='desc'):
    sort_by = request.args.get('sort_by', default_sort)
    sort_order = request.args.get('sort_order', default_order).lower()
    return sort_by, sort_order


def register_cli_commands(app):
    @app.cli.command('init-db')
    def init_db():
        from app.extensions import db
        db.create_all()
        print('Database initialized.')

    @app.cli.command('create-admin')
    def create_admin():
        from app.extensions import db
        from app.models import User, UserRole, UserStatus
        
        email = input('Admin email: ')
        password = input('Admin password: ')
        
        if User.query.filter_by(email=email).first():
            print('User already exists.')
            return
            
        admin = User(
            email=email,
            first_name='Admin',
            last_name='User',
            role=UserRole.ADMIN,
            status=UserStatus.ACTIVE,
            employee_id='ADMIN001',
            department='IT',
            designation='System Administrator'
        )
        admin.set_password(password)
        db.session.add(admin)
        db.session.commit()
        print(f'Admin user {email} created.')

    @app.cli.command('seed-data')
    def seed_data():
        from app.extensions import db
        from app.models import (
            Ship, ShipStatus, VesselType,
            Container, ContainerStatus, ContainerType,
            Truck, TruckStatus, TruckType,
            Equipment, EquipmentType, EquipmentStatus
        )
        from datetime import datetime, timedelta
        import random
        
        if Ship.query.count() > 0:
            print('Data already exists.')
            return
            
        vessels = [
            {'ship_id': 'MSC001', 'name': 'MSC Mediterranean', 'vessel_type': VesselType.CONTAINER_SHIP, 'flag': 'Panama', 'imo_number': 'IMO9876543', 'current_berth': 'Berth 1', 'status': ShipStatus.AT_BERTH, 'containers_onboard': 1200, 'max_containers': 2000},
            {'ship_id': 'MAE002', 'name': 'Maersk Essex', 'vessel_type': VesselType.CONTAINER_SHIP, 'flag': 'Denmark', 'imo_number': 'IMO9876544', 'current_berth': 'Berth 2', 'status': ShipStatus.AT_BERTH, 'containers_onboard': 800, 'max_containers': 1800},
            {'ship_id': 'CMA003', 'name': 'CMA CGM Brazil', 'vessel_type': VesselType.CONTAINER_SHIP, 'flag': 'France', 'imo_number': 'IMO9876545', 'current_berth': 'Berth 3', 'status': ShipStatus.APPROACHING, 'eta': datetime.utcnow() + timedelta(hours=4), 'containers_onboard': 1500, 'max_containers': 2200},
        ]
        for v in vessels:
            ship = Ship(**v)
            db.session.add(ship)
        db.session.flush()
        ship_ids = [s.id for s in Ship.query.all()]

        for i in range(1, 11):
            container = Container(
                container_id=f'MSKU{1000000+i}',
                iso_code='45G1',
                container_type=ContainerType.FORTY_FT_HC,
                status=random.choice(list(ContainerStatus)),
                weight=random.uniform(10000, 28000),
                max_weight=30480,
                owner='MSC',
                owner_code='MSCU',
                current_location=f'Block {random.randint(1,10)}-Bay {random.randint(1,40)}-Row {random.randint(1,20)}-Tier {random.randint(1,5)}',
                bay=str(random.randint(1,40)),
                row=str(random.randint(1,20)),
                tier=str(random.randint(1,5)),
                seal_number=f'SEAL{100000+i}',
                seal_status='INTACT',
                is_reefer=random.choice([True, False]),
                is_hazardous=random.choice([True, False]),
                customs_status='CLEARED',
                ship_id=random.choice(ship_ids) if random.choice([True, False]) else None,
            )
            db.session.add(container)
        db.session.flush()
        container_ids = [c.id for c in Container.query.all()]

        for i in range(1, 21):
            truck = Truck(
                truck_number=f'TN-{1000+i}',
                driver_name=f'Driver {i}',
                driver_phone=f'+91-9{random.randint(100000000, 999999999)}',
                truck_type=random.choice(list(TruckType)),
                status=random.choice(list(TruckStatus)),
                capacity=random.choice([20, 40]),
                assigned_container_id=random.choice(container_ids) if random.choice([True, False]) else None,
            )
            db.session.add(truck)
            
        equipments = [
            {'equipment_id': 'STS-01', 'name': 'STS Crane 1', 'equipment_type': EquipmentType.CRANE_STS, 'status': EquipmentStatus.OPERATIONAL, 'health_percentage': 95, 'location': 'Berth 1'},
            {'equipment_id': 'STS-02', 'name': 'STS Crane 2', 'equipment_type': EquipmentType.CRANE_STS, 'status': EquipmentStatus.OPERATIONAL, 'health_percentage': 92, 'location': 'Berth 2'},
            {'equipment_id': 'RTG-01', 'name': 'RTG Crane 1', 'equipment_type': EquipmentType.CRANE_RTG, 'status': EquipmentStatus.OPERATIONAL, 'health_percentage': 88, 'location': 'Block A'},
            {'equipment_id': 'RTG-02', 'name': 'RTG Crane 2', 'equipment_type': EquipmentType.CRANE_RTG, 'status': EquipmentStatus.MAINTENANCE, 'health_percentage': 45, 'location': 'Block B'},
            {'equipment_id': 'RS-01', 'name': 'Reach Stacker 1', 'equipment_type': EquipmentType.REACH_STACKER, 'status': EquipmentStatus.OPERATIONAL, 'health_percentage': 90, 'location': 'Yard 1'},
            {'equipment_id': 'TT-01', 'name': 'Terminal Tractor 1', 'equipment_type': EquipmentType.TERMINAL_TRACTOR, 'status': EquipmentStatus.OPERATIONAL, 'health_percentage': 93, 'location': 'Gate 1'},
        ]
        for e in equipments:
            eq = Equipment(**e)
            db.session.add(eq)
            
        db.session.commit()
        print('Sample data seeded successfully.')