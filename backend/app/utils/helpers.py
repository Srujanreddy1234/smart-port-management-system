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
            SecurityIncident, IncidentType, IncidentSeverity, IncidentStatus, SecurityZone, Alert, AlertType,
            MonitoringStation, AirQualityReading, WaterQualityReading, NoiseReading, WeatherReading, EmissionReading,
            MaintenanceSchedule, MaintenanceStatus, MaintenanceType, MaintenancePriority, ServiceLog,
            Invoice, InvoiceStatus, BillingLine, BillingCategory, PaymentMethod,
            EventLog, EventType, EventSeverity,
            Gate, GateType, GateStatus
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
            ('gates.read', 'View gates, congestion, and time slots', 'gates', 'read'),
            ('gates.book', 'Book/cancel own gate time slots', 'gates', 'book'),
            ('gates.manage', 'Manage gates and check in/complete any booking', 'gates', 'manage'),
        ]
        perms = {}
        for name, desc, module, action in permissions_data:
            p = Permission(name=name, description=desc, module=module, action=action, is_system=True)
            db.session.add(p)
            db.session.flush()
            perms[name] = p

        print('Creating roles...')
        # Derived from User.ROLE_PERMISSIONS (the single source of truth for
        # default role permissions) instead of a second hand-maintained copy
        # -- a prior duplicate here had drifted from the model's dict (e.g.
        # missing several .delete permissions for admin), which meant this
        # seed data disagreed with the app's own default permission set.
        role_permissions = {role.name.lower(): perms for role, perms in User.ROLE_PERMISSIONS.items()}
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
        import os
        password = os.environ.get('SEED_ADMIN_PASSWORD')
        if not password:
            password = 'admin123'
            print('WARNING: SEED_ADMIN_PASSWORD not set -- using the default demo')
            print('         password "admin123" for all seeded accounts, including')
            print('         Super Admin. Fine for local development; set a real')
            print('         SEED_ADMIN_PASSWORD before seeding a production database.')
        for email, first, last, role, dept, desig, eid in users_data:
            u = User(
                email=email, first_name=first, last_name=last,
                role=role, status=UserStatus.ACTIVE,
                employee_id=eid, department=dept, designation=desig,
                email_verified=True,
            )
            u.set_password(password)
            db.session.add(u)
        db.session.flush()

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
        db.session.flush()

        print('Creating gates...')
        gates_data = [
            ('GATE-1', 'Gate 1 - Container Terminal', GateType.CONTAINER, 'Terminal 1', 40, 8.7615, 77.8370),
            ('GATE-2', 'Gate 2 - Bulk Cargo', GateType.BULK_CARGO, 'Terminal 2', 24, 8.7660, 77.8410),
            ('GATE-3', 'Gate 3 - General / Mixed', GateType.GENERAL, 'Terminal 3', 20, 8.7700, 77.8330),
            ('GATE-4', 'Gate 4 - Tanker / Liquid Cargo', GateType.TANKER, 'Harbour', 16, 8.7580, 77.8450),
        ]
        for code, name, gtype, zone, cap, lat, lon in gates_data:
            g = Gate(
                gate_code=code, name=name, gate_type=gtype, status=GateStatus.OPEN,
                zone=zone, capacity_per_hour=cap, latitude=lat, longitude=lon, is_active=True,
            )
            db.session.add(g)
        db.session.flush()

        print('Creating monitoring stations...')
        stations = [
            ('MS-001', 'Main Terminal AQ Monitor', 'air_quality', 8.7642, 77.8363, 'Terminal 1'),
            ('MS-002', 'Harbour Water Monitor', 'water_quality', 8.7580, 77.8420, 'Harbour'),
            ('MS-003', 'Noise Monitor North', 'noise', 8.7690, 77.8300, 'North Zone'),
            ('MS-004', 'Weather Station', 'weather', 8.7600, 77.8400, 'Central'),
        ]
        for sid, name, stype, lat, lon, zone in stations:
            s = MonitoringStation(
                station_id=sid, name=name, station_type=stype,
                latitude=lat, longitude=lon, zone=zone, is_active=True,
            )
            db.session.add(s)
        db.session.flush()

        from seed_historical import seed_historical
        seed_historical(db, User, UserRole, UserStatus, Permission, Role,
                        Ship, ShipStatus, VesselType, Berth, BerthStatus,
                        Container, ContainerStatus, ContainerType,
                        Truck, TruckStatus, TruckType,
                        Equipment, EquipmentType, EquipmentStatus,
                        MaintenanceSchedule, MaintenanceStatus, MaintenanceType, MaintenancePriority, ServiceLog,
                        SecurityIncident, IncidentType, IncidentSeverity, IncidentStatus, SecurityZone, Alert, AlertType,
                        MonitoringStation, AirQualityReading, WaterQualityReading, NoiseReading, WeatherReading, EmissionReading,
                        Invoice, InvoiceStatus, BillingLine, BillingCategory, PaymentMethod,
                        EventLog, EventType, EventSeverity)

        db.session.commit()
        print('All seed data created successfully.')
        print(f'Demo credentials (password: {"admin123" if password == "admin123" else "<value of SEED_ADMIN_PASSWORD>"}):')
        for email, first, last, role, dept, desig, eid in users_data:
            print(f'  {email} ({role.value})')

    @app.cli.command('backfill-water-quality')
    def backfill_water_quality():
        """Populate WaterQualityReading, which -- unlike weather/air quality
        (real ERA5/CAMS data via datasets/scripts/import_to_database.py) or
        noise (seeded by seed_historical.py's main flow) -- has never been
        populated at all in some environments. Safe to run against a
        database that already has users/ships/etc: unlike `seed-data`, it
        only touches the water_quality monitoring station's readings, and
        is a no-op if that station already has any rows.
        """
        from app.extensions import db
        from app.models import MonitoringStation, WaterQualityReading
        from datetime import datetime, timedelta
        import random

        random.seed(42)
        station = MonitoringStation.query.filter_by(station_type='water_quality').first()
        if not station:
            print('No water_quality monitoring station found -- nothing to backfill.')
            return

        existing = WaterQualityReading.query.filter_by(station_id=station.id).count()
        if existing > 0:
            print(f'WaterQualityReading already has {existing} rows for station {station.station_id} -- skipping.')
            return

        now = datetime.utcnow()
        seven_years_ago = now - timedelta(days=7 * 365)
        current = seven_years_ago
        created = 0
        while current <= now:
            if random.random() < 0.3:
                db.session.add(WaterQualityReading(
                    station_id=station.id,
                    ph=random.uniform(7.5, 8.4),
                    dissolved_oxygen=random.uniform(4.5, 8.0),
                    bod=random.uniform(1.0, 5.0),
                    cod=random.uniform(10, 40),
                    tss=random.uniform(10, 60),
                    tds=random.uniform(30000, 36000),
                    oil_grease=random.uniform(0.5, 4.0),
                    ammonia=random.uniform(0.05, 0.5),
                    nitrate=random.uniform(0.1, 2.0),
                    phosphate=random.uniform(0.02, 0.3),
                    temperature=random.uniform(26, 32),
                    turbidity=random.uniform(2, 20),
                    conductivity=random.uniform(45000, 55000),
                    salinity=random.uniform(32, 36),
                    fecal_coliform=random.uniform(0, 200),
                    total_coliform=random.uniform(0, 500),
                    phenols=random.uniform(0, 0.01),
                    cyanide=random.uniform(0, 0.005),
                    sulfide=random.uniform(0, 0.05),
                    recorded_at=current,
                ))
                created += 1
            current += timedelta(days=1)

        db.session.commit()
        print(f'Backfilled {created} WaterQualityReading rows for station {station.station_id}.')