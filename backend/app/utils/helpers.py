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

    @app.cli.command('seed-data')
    def seed_data():
        from app.extensions import db
        from app.models import (
            User, UserRole, UserStatus, Permission, Role,
            Ship, ShipStatus, VesselType, Berth, BerthStatus,
            Container, ContainerStatus, ContainerType,
            Truck, TruckStatus, TruckType,
            Equipment, EquipmentType, EquipmentStatus,
            SecurityIncident, IncidentType, IncidentSeverity, IncidentStatus, SecurityZone,
            MonitoringStation, AirQualityReading, WeatherReading,
        )
        from datetime import datetime, timedelta
        import random

        if User.query.count() > 0:
            print('Data already exists. Skipping seed.')
            return

        print('Creating permissions...')
        permissions_data = [
            ('all', 'Full system access', 'system', 'all'),
            ('dashboard.read', 'View dashboard', 'dashboard', 'read'),
            ('dashboard.write', 'Customize dashboard', 'dashboard', 'write'),
            ('ships.read', 'View ships', 'ships', 'read'),
            ('ships.write', 'Create/edit ships', 'ships', 'write'),
            ('ships.delete', 'Delete ships', 'ships', 'delete'),
            ('containers.read', 'View containers', 'containers', 'read'),
            ('containers.write', 'Create/edit containers', 'containers', 'write'),
            ('containers.delete', 'Delete containers', 'containers', 'delete'),
            ('trucks.read', 'View trucks', 'trucks', 'read'),
            ('trucks.write', 'Create/edit trucks', 'trucks', 'write'),
            ('trucks.delete', 'Delete trucks', 'trucks', 'delete'),
            ('berths.read', 'View berths', 'berths', 'read'),
            ('berths.write', 'Manage berths', 'berths', 'write'),
            ('berths.delete', 'Delete berths', 'berths', 'delete'),
            ('security.read', 'View security', 'security', 'read'),
            ('security.write', 'Manage security', 'security', 'write'),
            ('security.delete', 'Delete security incidents', 'security', 'delete'),
            ('maintenance.read', 'View maintenance', 'maintenance', 'read'),
            ('maintenance.write', 'Manage maintenance', 'maintenance', 'write'),
            ('maintenance.delete', 'Delete maintenance records', 'maintenance', 'delete'),
            ('environment.read', 'View environmental data', 'environment', 'read'),
            ('environment.write', 'Manage environmental data', 'environment', 'write'),
            ('environment.delete', 'Delete environmental data', 'environment', 'delete'),
            ('reports.read', 'View reports', 'reports', 'read'),
            ('reports.write', 'Create reports', 'reports', 'write'),
            ('reports.delete', 'Delete reports', 'reports', 'delete'),
            ('users.read', 'View users', 'users', 'read'),
            ('users.write', 'Create/edit users', 'users', 'write'),
            ('users.delete', 'Delete users', 'users', 'delete'),
            ('roles.read', 'View roles', 'roles', 'read'),
            ('roles.write', 'Create/edit roles', 'roles', 'write'),
            ('roles.delete', 'Delete roles', 'roles', 'delete'),
            ('audit.read', 'View audit logs', 'audit', 'read'),
            ('settings.read', 'View settings', 'settings', 'read'),
            ('settings.write', 'Modify settings', 'settings', 'write'),
        ]
        perms = {}
        for name, desc, module, action in permissions_data:
            p = Permission(name=name, description=desc, module=module, action=action, is_system=True)
            db.session.add(p)
            db.session.flush()
            perms[name] = p

        print('Creating roles...')
        role_permissions = {
            'super_admin': ['all'],
            'admin': [
                'users.read', 'users.write', 'users.delete',
                'roles.read', 'roles.write',
                'ships.read', 'ships.write', 'ships.delete',
                'containers.read', 'containers.write', 'containers.delete',
                'trucks.read', 'trucks.write', 'trucks.delete',
                'berths.read', 'berths.write',
                'dashboard.read', 'dashboard.write',
                'reports.read', 'reports.write', 'reports.delete',
                'maintenance.read', 'maintenance.write',
                'security.read', 'security.write',
                'environment.read', 'environment.write',
                'audit.read', 'settings.read', 'settings.write',
            ],
            'port_supervisor': [
                'ships.read', 'ships.write',
                'containers.read', 'containers.write',
                'trucks.read', 'trucks.write',
                'berths.read', 'berths.write',
                'dashboard.read', 'reports.read',
                'maintenance.read', 'maintenance.write',
                'security.read', 'security.write',
                'environment.read', 'audit.read',
            ],
            'port_staff': [
                'ships.read', 'ships.write',
                'containers.read', 'containers.write',
                'trucks.read', 'trucks.write',
                'berths.read',
                'dashboard.read', 'reports.read',
                'maintenance.read', 'maintenance.write',
                'security.read',
            ],
            'customs_officer': [
                'containers.read', 'containers.write',
                'trucks.read', 'ships.read',
                'dashboard.read', 'reports.read', 'security.read',
            ],
            'shipping_company': [
                'ships.read', 'containers.read', 'containers.write',
                'trucks.read', 'dashboard.read', 'reports.read', 'berths.read',
            ],
            'truck_operator': [
                'trucks.read', 'trucks.write',
                'containers.read', 'ships.read', 'dashboard.read', 'reports.read',
            ],
            'customer': [
                'containers.read', 'ships.read', 'dashboard.read', 'reports.read',
            ],
            'public': [
                'ships.read', 'dashboard.read',
            ],
        }
        role_names = {
            'super_admin': 'Super Admin',
            'admin': 'Admin',
            'port_supervisor': 'Port Supervisor',
            'port_staff': 'Port Staff',
            'customs_officer': 'Customs Officer',
            'shipping_company': 'Shipping Company',
            'truck_operator': 'Truck Operator',
            'customer': 'Customer',
            'public': 'Public',
        }
        roles = {}
        for key, display in role_names.items():
            r = Role(name=key, display_name=display, is_system=True)
            db.session.add(r)
            db.session.flush()
            roles[key] = r
            for pname in role_permissions.get(key, []):
                if pname in perms:
                    r.permissions.append(perms[pname])

        print('Creating users for all 9 roles...')
        users_data = [
            ('superadmin@smartport.gov.in', 'Super', 'Admin', UserRole.SUPER_ADMIN, 'IT', 'Super Administrator', 'ADMIN001'),
            ('admin@smartport.gov.in', 'Rajesh', 'Kumar', UserRole.ADMIN, 'Management', 'Port Director', 'ADMIN002'),
            ('supervisor@smartport.gov.in', 'Priya', 'Sharma', UserRole.PORT_SUPERVISOR, 'Operations', 'Operations Supervisor', 'OPS001'),
            ('staff@smartport.gov.in', 'Arjun', 'Patel', UserRole.PORT_STAFF, 'Operations', 'Port Operator', 'OPS002'),
            ('customs@smartport.gov.in', 'Lakshmi', 'Nair', UserRole.CUSTOMS_OFFICER, 'Customs', 'Customs Inspector', 'CUS001'),
            ('shipping@smartport.gov.in', 'Vikram', 'Singh', UserRole.SHIPPING_COMPANY, 'Shipping', 'Fleet Manager', 'SHP001'),
            ('truck@smartport.gov.in', 'Murugan', 'Raja', UserRole.TRUCK_OPERATOR, 'Transport', 'Truck Driver', 'TRK001'),
            ('customer@smartport.gov.in', 'Ananya', 'Reddy', UserRole.CUSTOMER, 'Client', 'Account Manager', 'CUS002'),
            ('public@smartport.gov.in', 'Demo', 'User', UserRole.PUBLIC, 'Public', 'Visitor', 'PUB001'),
        ]
        password = 'admin123'
        for email, first, last, role, dept, desig, eid in users_data:
            u = User(
                email=email, first_name=first, last_name=last,
                role=role, status=UserStatus.ACTIVE,
                employee_id=eid, department=dept, designation=desig,
                email_verified=True,
            )
            u.set_password(password)
            db.session.add(u)

        print('Creating berths...')
        berths_data = [
            ('BERTH-01', 'Berth 1', 'B1', BerthStatus.OCCUPIED, 350, 50, 16.5, 120000, 8000, 18.0, 350, True, 65, 'Terminal 1', 'Main'),
            ('BERTH-02', 'Berth 2', 'B2', BerthStatus.OCCUPIED, 320, 45, 14.5, 100000, 6000, 16.0, 320, True, 50, 'Terminal 1', 'Main'),
            ('BERTH-03', 'Berth 3', 'B3', BerthStatus.AVAILABLE, 300, 42, 13.0, 80000, 5000, 15.0, 300, True, 45, 'Terminal 1', 'Main'),
            ('BERTH-04', 'Berth 4', 'B4', BerthStatus.AVAILABLE, 280, 40, 12.0, 60000, 4000, 14.0, 280, True, 40, 'Terminal 2', 'East'),
            ('BERTH-05', 'Berth 5', 'B5', BerthStatus.AVAILABLE, 260, 38, 11.0, 50000, 3500, 13.0, 260, True, 35, 'Terminal 2', 'East'),
            ('BERTH-06', 'Berth 6', 'B6', BerthStatus.MAINTENANCE, 300, 42, 13.0, 80000, 5000, 15.0, 300, True, 45, 'Terminal 2', 'East'),
            ('BERTH-07', 'Berth 7', 'B7', BerthStatus.AVAILABLE, 240, 35, 10.0, 40000, 3000, 12.0, 240, False, 0, 'Terminal 3', 'West'),
            ('BERTH-08', 'Berth 8', 'B8', BerthStatus.AVAILABLE, 220, 32, 9.0, 30000, 2500, 11.0, 220, False, 0, 'Terminal 3', 'West'),
            ('BERTH-09', 'Berth 9', 'B9', BerthStatus.AVAILABLE, 200, 30, 8.0, 25000, 2000, 10.0, 200, False, 0, 'Terminal 3', 'West'),
        ]
        for bid, name, code, status, ml, mb, md, mt, mc, depth, length, hc, cc, zone, terminal in berths_data:
            berth = Berth(
                berth_id=bid, name=name, code=code, status=status,
                max_length=ml, max_beam=mb, max_draft=md, max_tonnage=mt,
                max_containers=mc, depth=depth, length=length,
                has_crane=hc, crane_capacity=cc, zone=zone, terminal=terminal,
            )
            db.session.add(berth)

        print('Creating ships...')
        ships_data = [
            ('MSC001', 'MSC Mediterranean', VesselType.CONTAINER_SHIP, 'Panama', 'IMO9876543', 366, 51, 14.5, 165000, 180000, 18000, ShipStatus.AT_BERTH, 'Berth 1', datetime.utcnow() - timedelta(hours=2), datetime.utcnow() + timedelta(hours=12), 'MSC Shipping', 1200, 200, 100),
            ('MAE002', 'Maersk Essex', VesselType.CONTAINER_SHIP, 'Denmark', 'IMO9876544', 350, 48, 13.8, 155000, 170000, 15000, ShipStatus.AT_BERTH, 'Berth 2', datetime.utcnow() - timedelta(hours=6), datetime.utcnow() + timedelta(hours=18), 'Maersk Line', 800, 150, 100),
            ('CMA003', 'CMA CGM Brazil', VesselType.CONTAINER_SHIP, 'France', 'IMO9876545', 398, 54, 16.0, 180000, 200000, 20000, ShipStatus.APPROACHING, None, datetime.utcnow() + timedelta(hours=4), None, 'CMA CGM', 1500, 0, 500),
            ('COS004', 'COSCO Fortune', VesselType.CONTAINER_SHIP, 'China', 'IMO9876546', 400, 58, 16.5, 195000, 220000, 22000, ShipStatus.ANCHORED, None, datetime.utcnow() + timedelta(hours=8), None, 'COSCO', 0, 800, 0),
            ('MSC005', 'MSC Diana', VesselType.BULK_CARRIER, 'Panama', 'IMO9876547', 289, 45, 18.2, 200000, 205000, 0, ShipStatus.SCHEDULED, None, datetime.utcnow() + timedelta(days=2), None, 'MSC Shipping', 0, 0, 0),
            ('EVE006', 'Ever Given', VesselType.CONTAINER_SHIP, 'Panama', 'IMO9876548', 400, 59, 16.0, 220000, 220000, 20000, ShipStatus.IN_CHANNEL, None, datetime.utcnow() + timedelta(hours=1), None, 'Evergreen', 0, 300, 0),
            ('BWL007', 'BWLR Glacier', VesselType.TANKER, 'Norway', 'IMO9876549', 333, 60, 20.5, 160000, 300000, 0, ShipStatus.AT_BERTH, 'Berth 5', datetime.utcnow() - timedelta(hours=10), datetime.utcnow() + timedelta(hours=14), 'BW Liquefied', 0, 0, 0),
            ('TNK008', 'MT Chennai', VesselType.TANKER, 'India', 'IMO9876550', 183, 32, 10.0, 45000, 80000, 0, ShipStatus.DEPARTED, None, None, datetime.utcnow() - timedelta(hours=3), 'Indian Oil Corp', 0, 0, 0),
            ('RR009', 'Celtic Warrior', VesselType.RO_RO, 'Ireland', 'IMO9876551', 199, 30, 8.0, 30000, 45000, 0, ShipStatus.APPROACHING, None, datetime.utcnow() + timedelta(hours=6), None, 'Celtic Shipping', 0, 0, 0),
            ('TUG010', 'Harbour Tiger', VesselType.TUG, 'India', 'IMO9876552', 35, 12, 5.0, 500, 500, 0, ShipStatus.AT_BERTH, 'Berth 1', None, None, 'Port Authority', 0, 0, 0),
        ]
        ship_ids = []
        for sid, name, vtype, flag, imo, loa, beam, draft, gt, dwt, mc, status, berth, eta, etd, agent, co, ctl, ctd in ships_data:
            ship = Ship(
                ship_id=sid, name=name, vessel_type=vtype, flag=flag,
                imo_number=imo, length_overall=loa, beam=beam, draft=draft,
                gross_tonnage=gt, deadweight_tonnage=dwt, max_containers=mc,
                status=status, current_berth=berth, eta=eta, etd=etd,
                agent=agent, containers_onboard=co, containers_to_load=ctl,
                containers_to_discharge=ctd,
                ata=datetime.utcnow() - timedelta(hours=random.randint(1, 24)) if status in [ShipStatus.AT_BERTH, ShipStatus.LOADING, ShipStatus.UNLOADING] else None,
            )
            db.session.add(ship)
            db.session.flush()
            ship_ids.append(ship.id)

        print('Creating containers...')
        container_statuses = list(ContainerStatus)
        for i in range(1, 51):
            c = Container(
                container_id=f'MSKU{1000000+i}',
                iso_code=random.choice(['20G1', '40G1', '45G1', '45R1', '22H1']),
                container_type=random.choice(list(ContainerType)),
                status=random.choice(container_statuses),
                weight=random.uniform(2000, 28000),
                max_weight=30480,
                owner=random.choice(['MSC', 'Maersk', 'CMA CGM', 'COSCO', 'Evergreen']),
                owner_code=random.choice(['MSCU', 'MAEU', 'CMAU', 'COSU', 'EGLU']),
                current_location=f'Block {random.randint(1,10)}-Bay {random.randint(1,40)}-Row {random.randint(1,20)}-Tier {random.randint(1,5)}',
                bay=str(random.randint(1, 40)),
                row=str(random.randint(1, 20)),
                tier=str(random.randint(1, 5)),
                seal_number=f'SEAL{100000+i}',
                seal_status='INTACT',
                is_reefer=random.random() < 0.15,
                is_hazardous=random.random() < 0.05,
                customs_status=random.choice(['CLEARED', 'PENDING', 'HOLD']),
                ship_id=random.choice(ship_ids),
                gate_in_at=datetime.utcnow() - timedelta(hours=random.randint(1, 72)),
            )
            db.session.add(c)

        print('Creating trucks...')
        for i in range(1, 31):
            t = Truck(
                truck_number=f'TN-{1000+i}',
                driver_name=random.choice(['Raja', 'Kumar', 'Murugan', 'Selvam', 'Anbu', 'Mani', 'Karthik', 'Suresh', 'Ravi', 'Prakash']),
                driver_phone=f'+91-9{random.randint(100000000, 999999999)}',
                truck_type=random.choice(list(TruckType)),
                status=random.choice([TruckStatus.AVAILABLE, TruckStatus.IN_TRANSIT, TruckStatus.AT_GATE, TruckStatus.LOADING]),
                capacity=random.choice([20, 40]),
                license_plate=f'TN-{random.randint(10,99)}-{chr(65+random.randint(0,25))}{chr(65+random.randint(0,25))}-{random.randint(1000,9999)}',
            )
            db.session.add(t)

        print('Creating equipment...')
        equip_data = [
            ('STS-01', 'STS Crane 1', EquipmentType.CRANE_STS, EquipmentStatus.OPERATIONAL, 95, 'Berth 1'),
            ('STS-02', 'STS Crane 2', EquipmentType.CRANE_STS, EquipmentStatus.OPERATIONAL, 92, 'Berth 2'),
            ('STS-03', 'STS Crane 3', EquipmentType.CRANE_STS, EquipmentStatus.MAINTENANCE, 45, 'Berth 6'),
            ('RTG-01', 'RTG Crane 1', EquipmentType.CRANE_RTG, EquipmentStatus.OPERATIONAL, 88, 'Block A'),
            ('RTG-02', 'RTG Crane 2', EquipmentType.CRANE_RTG, EquipmentStatus.OPERATIONAL, 91, 'Block B'),
            ('RTG-03', 'RTG Crane 3', EquipmentType.CRANE_RTG, EquipmentStatus.OPERATIONAL, 78, 'Block C'),
            ('RS-01', 'Reach Stacker 1', EquipmentType.REACH_STACKER, EquipmentStatus.OPERATIONAL, 90, 'Yard 1'),
            ('RS-02', 'Reach Stacker 2', EquipmentType.REACH_STACKER, EquipmentStatus.STANDBY, 75, 'Yard 2'),
            ('TT-01', 'Terminal Tractor 1', EquipmentType.TERMINAL_TRACTOR, EquipmentStatus.OPERATIONAL, 93, 'Gate 1'),
            ('TT-02', 'Terminal Tractor 2', EquipmentType.TERMINAL_TRACTOR, EquipmentStatus.OPERATIONAL, 89, 'Gate 2'),
            ('FK-01', 'Forklift 1', EquipmentType.FORKLIFT, EquipmentStatus.OPERATIONAL, 85, 'Warehouse 1'),
            ('FK-02', 'Forklift 2', EquipmentType.FORKLIFT, EquipmentStatus.MAINTENANCE, 35, 'Warehouse 2'),
        ]
        for eid, name, etype, status, health, loc in equip_data:
            eq = Equipment(
                equipment_id=eid, name=name, equipment_type=etype,
                status=status, health_percentage=health, location=loc,
                operating_hours=random.randint(500, 15000),
                last_service_date=datetime.utcnow() - timedelta(days=random.randint(7, 90)),
                next_service_date=datetime.utcnow() + timedelta(days=random.randint(7, 90)),
            )
            db.session.add(eq)

        print('Creating security incidents...')
        incident_data = [
            ('INC-001', IncidentType.UNAUTHORIZED_ACCESS, SecurityZone.ZONE_B, IncidentSeverity.HIGH, IncidentStatus.ACTIVE, 'Unauthorized access near Berth 7', datetime.utcnow() - timedelta(minutes=30)),
            ('INC-002', IncidentType.SUSPICIOUS_ACTIVITY, SecurityZone.ZONE_C, IncidentSeverity.MEDIUM, IncidentStatus.INVESTIGATING, 'Suspicious vehicle near Gate 2', datetime.utcnow() - timedelta(hours=2)),
            ('INC-003', IncidentType.VIOLATION, SecurityZone.ZONE_A, IncidentSeverity.LOW, IncidentStatus.RESOLVED, 'Speed limit violation in terminal', datetime.utcnow() - timedelta(hours=6)),
        ]
        for iid, itype, zone, sev, status, desc, detected in incident_data:
            inc = SecurityIncident(
                incident_id=iid, incident_type=itype, zone=zone,
                severity=sev, status=status, title=desc,
                description=desc, detected_at=detected,
            )
            db.session.add(inc)

        print('Creating monitoring stations and readings...')
        stations = [
            ('MS-001', 'Main Terminal AQ Monitor', 'air_quality', 8.7642, 77.8363, 'Terminal 1'),
            ('MS-002', 'Harbour Water Monitor', 'water_quality', 8.7580, 77.8420, 'Harbour'),
            ('MS-003', 'Noise Monitor North', 'noise', 8.7690, 77.8300, 'North Zone'),
            ('MS-004', 'Weather Station', 'weather', 8.7600, 77.8400, 'Central'),
        ]
        station_ids = []
        for sid, name, stype, lat, lon, zone in stations:
            s = MonitoringStation(
                station_id=sid, name=name, station_type=stype,
                latitude=lat, longitude=lon, zone=zone, is_active=True,
            )
            db.session.add(s)
            db.session.flush()
            station_ids.append(s.id)

        for sid in station_ids:
            for h in range(24):
                ts = datetime.utcnow().replace(minute=0, second=0, microsecond=0) - timedelta(hours=23-h)
                aq = AirQualityReading(
                    station_id=sid, aqi=random.randint(20, 80),
                    pm25=random.uniform(5, 35), pm10=random.uniform(10, 50),
                    no2=random.uniform(5, 30), co=random.uniform(0.3, 1.2),
                    temperature=random.uniform(28, 36), humidity=random.uniform(60, 85),
                    wind_speed=random.uniform(5, 25), recorded_at=ts,
                )
                db.session.add(aq)
                w = WeatherReading(
                    station_id=sid, temperature=random.uniform(28, 36),
                    humidity=random.uniform(60, 85), wind_speed=random.uniform(5, 25),
                    pressure=random.uniform(1008, 1015), weather_condition=random.choice(['Partly Cloudy', 'Sunny', 'Cloudy', 'Light Rain']),
                    recorded_at=ts,
                )
                db.session.add(w)

        db.session.commit()
        print('All seed data created successfully.')
        print('Demo credentials (password: admin123):')
        for email, first, last, role, dept, desig, eid in users_data:
            print(f'  {email} ({role.value})')