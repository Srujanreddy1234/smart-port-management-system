from datetime import datetime, timedelta
import random

random.seed(42)

def seed_historical(db, User, UserRole, UserStatus, Permission, Role,
                    Ship, ShipStatus, VesselType, Berth, BerthStatus,
                    Container, ContainerStatus, ContainerType,
                    Truck, TruckStatus, TruckType,
                    Equipment, EquipmentType, EquipmentStatus,
                    MaintenanceSchedule, MaintenanceStatus, MaintenanceType, MaintenancePriority,
                    ServiceLog,
                    SecurityIncident, IncidentType, IncidentSeverity, IncidentStatus, SecurityZone, Alert, AlertType,
                    MonitoringStation, AirQualityReading, WaterQualityReading, NoiseReading, WeatherReading, EmissionReading,
                    Invoice, InvoiceStatus, BillingLine, BillingCategory, PaymentMethod,
                    EventLog, EventType, EventSeverity):
    now = datetime.utcnow()
    seven_years_ago = now - timedelta(days=7*365)

    users = User.query.all()
    user_ids = [u.id for u in users]
    berths = Berth.query.all()
    berth_ids = [b.id for b in berths]

    ship_names = [
        'MSC Mediterranean', 'Maersk Essex', 'CMA CGM Brazil', 'COSCO Fortune', 'Ever Given',
        'BWLR Glacier', 'Harbour Tiger', 'MT Chennai', 'Celtic Warrior', 'MV Pacific Star',
        'Ocean Star', 'Blue Marlin', 'Golden Horizon', 'Silver Wave', 'Iron Dragon',
        'Swift Gull', 'Northern Light', 'Southern Cross', 'Eastern Promise', 'Western Wind',
        'Coral Queen', 'Pearl Ace', 'Jade Emperor', 'Ruby Princess', 'Sapphire King',
        'Diamond Queen', 'Emerald Bay', 'Ocean Pioneer', 'Sea Guardian', 'Port Hope',
        'Harbour Master', 'Tidal Wave', 'Deep Blue', 'Trade Winds', 'Cargo Master',
        'Bay Express', 'Coastal King', 'Marine Angel', 'Ocean Chief', 'Port Royal',
        'Sea Breeze', 'Titanic Spirit', 'Voyager', 'Zenith Star', 'Atlantic Wave',
        'Pacific Dream', 'Indian Pearl', 'Arctic Fox', 'Desert Rose', 'Forest King'
    ]
    flags = ['Panama', 'Liberia', 'Marshall Islands', 'Hong Kong', 'Singapore', 'India', 'Denmark', 'France', 'China', 'Norway', 'UK', 'Malta', 'Greece', 'Japan', 'South Korea']
    agents = ['MSC Shipping', 'Maersk Line', 'CMA CGM', 'COSCO', 'Evergreen', 'SCI', 'BW Liquefied', 'Port Authority', 'Mediterranean Shipping Co.', 'A.P. Moller-Maersk']
    vessel_types = list(VesselType)
    statuses = list(ShipStatus)

    print('Creating ships...')
    ships = []
    for i in range(300):
        name = ship_names[i % len(ship_names)] + (f' {i//50 + 1}' if i >= 50 else '')
        vtype = random.choice(vessel_types)
        status = random.choice(statuses)
        eta = seven_years_ago + timedelta(days=random.randint(0, 2555))
        etd = eta + timedelta(days=random.randint(1, 14)) if eta else None
        berth = random.choice(berth_ids) if status in [ShipStatus.AT_BERTH, ShipStatus.LOADING, ShipStatus.UNLOADING] else None
        ship = Ship(
            ship_id=f'SH-{2019 + random.randint(0, 7)}-{i+1:04d}',
            name=name,
            vessel_type=vtype,
            flag=random.choice(flags),
            imo_number=f'IMO{9300000 + i}',
            mmsi=f'{412000000 + i}',
            call_sign=f'V{random.randint(1000, 9999)}',
            length_overall=random.uniform(100, 400),
            beam=random.uniform(15, 60),
            draft=random.uniform(5, 20),
            gross_tonnage=random.randint(5000, 220000),
            deadweight_tonnage=random.randint(8000, 240000),
            max_containers=random.randint(0, 20000) if vtype == VesselType.CONTAINER_SHIP else 0,
            status=status,
            current_berth=f'Berth {berth}' if berth else None,
            eta=eta,
            etd=etd,
            ata=eta - timedelta(hours=random.randint(0, 4)) if status in [ShipStatus.AT_BERTH, ShipStatus.LOADING, ShipStatus.UNLOADING] and eta else None,
            atd=etd + timedelta(hours=random.randint(0, 6)) if status == ShipStatus.DEPARTED and etd else None,
            agent=random.choice(agents),
            agent_contact=f'+91-9{random.randint(100000000, 999999999)}',
            agent_email=f'ops@{random.choice(agents).lower().replace(" ", "")}.com',
            containers_onboard=random.randint(0, 15000) if vtype == VesselType.CONTAINER_SHIP else 0,
            containers_to_load=random.randint(0, 5000),
            containers_to_discharge=random.randint(0, 5000),
            created_at=eta - timedelta(days=random.randint(1, 30)) if eta else seven_years_ago,
        )
        db.session.add(ship)
        db.session.flush()
        ships.append(ship)

    print('Creating containers...')
    container_statuses = list(ContainerStatus)
    container_types = list(ContainerType)
    owners = ['MSC', 'Maersk', 'CMA CGM', 'COSCO', 'Evergreen', 'SCI', 'HMM', 'OOCL', 'Yang Ming', 'Hapag']
    owner_codes = ['MSCU', 'MAEU', 'CMAU', 'COSU', 'EGLU', 'SCIU', 'HMMU', 'OOLU', 'YMLU', 'HLCU']
    ports = ['Colombo', 'Singapore', 'Dubai', 'Hong Kong', 'Shanghai', 'Mumbai', 'Chennai', 'Kolkata', 'Bangkok', 'Jakarta']

    for i in range(1500):
        ship = random.choice(ships) if ships else None
        status = random.choice(container_statuses)
        gate_in = seven_years_ago + timedelta(days=random.randint(0, 2555), hours=random.randint(0, 23))
        gate_out = gate_in + timedelta(days=random.randint(1, 14)) if status in [ContainerStatus.IN_TRANSIT, ContainerStatus.DELIVERED] else None
        c = Container(
            container_id=f'CONT-{i+1:06d}',
            iso_code=random.choice(['20G1', '40G1', '45G1', '45R1', '22H1', '40H1', '20R1']),
            container_type=random.choice(container_types),
            status=status,
            weight=random.uniform(2000, 28000),
            max_weight=random.choice([30480, 24000, 21600]),
            owner=random.choice(owners),
            owner_code=random.choice(owner_codes),
            ship_id=ship.id if ship else None,
            origin_port=random.choice(ports),
            destination_port=random.choice(ports),
            current_location=f'Block {random.randint(1,10)}-Bay {random.randint(1,40)}-Row {random.randint(1,20)}-Tier {random.randint(1,5)}',
            bay=str(random.randint(1, 40)),
            row=str(random.randint(1, 20)),
            tier=str(random.randint(1, 5)),
            seal_number=f'SEAL{100000+i}',
            seal_status='INTACT',
            temperature=random.uniform(-20, 20) if random.random() < 0.15 else None,
            is_reefer=random.random() < 0.15,
            is_hazardous=random.random() < 0.05,
            hazardous_class=random.choice(['2.1', '3', '4.1', '5.1', '6.1', '8', '9']) if random.random() < 0.05 else None,
            customs_status=random.choice(['CLEARED', 'PENDING', 'HOLD', 'RELEASED']),
            gate_in_at=gate_in,
            gate_out_at=gate_out,
            created_at=gate_in - timedelta(days=random.randint(1, 7)),
        )
        db.session.add(c)

    print('Creating trucks...')
    driver_names = ['Raja', 'Kumar', 'Murugan', 'Selvam', 'Anbu', 'Mani', 'Karthik', 'Suresh', 'Ravi', 'Prakash', 'Vijay', 'Arun', 'Senthil', 'Ganesh', 'Ramesh', 'Mohan', 'Raj', 'Krishnan', 'Bala', 'Devi']
    truck_statuses = list(TruckStatus)
    truck_types = list(TruckType)
    for i in range(600):
        status = random.choice(truck_statuses)
        gate_in = seven_years_ago + timedelta(days=random.randint(0, 2555), hours=random.randint(0, 23))
        gate_out = gate_in + timedelta(hours=random.randint(1, 8)) if status == TruckStatus.IN_TRANSIT else None
        t = Truck(
            truck_number=f'TN-{1000+i}',
            driver_name=random.choice(driver_names),
            driver_phone=f'+91-9{random.randint(100000000, 999999999)}',
            truck_type=random.choice(truck_types),
            status=status,
            capacity=random.choice([20, 40]),
            license_plate=f'TN-{random.randint(10,99)}-{chr(65+random.randint(0,25))}{chr(65+random.randint(0,25))}-{random.randint(1000,9999)}',
            chassis_number=f'CH{random.randint(100000, 999999)}',
            owner=random.choice(['Port Authority', 'Private Contractor', 'Logistics Co.', 'Transport Ltd.']),
            owner_contact=f'+91-9{random.randint(100000000, 999999999)}',
            current_location=random.choice(['Gate 1', 'Gate 2', 'Yard', 'Berth 1', 'Berth 2', 'Berth 3', 'Warehouse', 'Outside']),
            gate_in_time=gate_in,
            gate_out_time=gate_out,
            created_at=gate_in - timedelta(days=random.randint(0, 3)),
        )
        db.session.add(t)

    print('Creating equipment...')
    equip_data = []
    for i in range(40):
        etype = random.choice(list(EquipmentType))
        status = random.choice([EquipmentStatus.OPERATIONAL, EquipmentStatus.OPERATIONAL, EquipmentStatus.OPERATIONAL, EquipmentStatus.MAINTENANCE, EquipmentStatus.STANDBY])
        eq = Equipment(
            equipment_id=f'EQ-{i+1:03d}',
            name=f'{etype.value} {i+1}',
            equipment_type=etype,
            manufacturer=random.choice(['ZPMC', 'Kalmar', 'Konecranes', 'Liebherr', 'Caterpillar', 'Toyota', 'Hyster', 'Mitsubishi']),
            model=f'Model-{random.randint(100, 999)}',
            serial_number=f'SN{random.randint(100000, 999999)}',
            year_manufactured=random.randint(2010, 2023),
            location=random.choice(['Berth 1', 'Berth 2', 'Berth 3', 'Block A', 'Block B', 'Block C', 'Yard 1', 'Gate 1', 'Warehouse 1']),
            zone=random.choice(['Zone A', 'Zone B', 'Zone C', 'Zone D']),
            status=status,
            health_percentage=random.randint(30, 100) if status == EquipmentStatus.OPERATIONAL else random.randint(10, 60),
            operating_hours=random.uniform(1000, 25000),
            last_service_date=now - timedelta(days=random.randint(7, 180)),
            next_service_date=now + timedelta(days=random.randint(7, 180)),
            last_inspection_date=now - timedelta(days=random.randint(30, 365)),
            next_inspection_date=now + timedelta(days=random.randint(30, 365)),
            created_at=seven_years_ago + timedelta(days=random.randint(0, 365)),
        )
        db.session.add(eq)
        db.session.flush()
        equip_data.append(eq)

    print('Creating maintenance schedules...')
    for eq in equip_data:
        for _ in range(random.randint(3, 8)):
            sched_date = seven_years_ago + timedelta(days=random.randint(0, 2555))
            mstatus = random.choice([MaintenanceStatus.COMPLETED, MaintenanceStatus.COMPLETED, MaintenanceStatus.COMPLETED, MaintenanceStatus.SCHEDULED, MaintenanceStatus.IN_PROGRESS])
            ms = MaintenanceSchedule(
                equipment_id=eq.id,
                maintenance_type=random.choice(list(MaintenanceType)),
                priority=random.choice(list(MaintenancePriority)),
                status=mstatus,
                title=f'{random.choice(["Preventive", "Corrective", "Inspection"])} maintenance on {eq.name}',
                description=f'Routine {random.choice(["oil change", "parts replacement", "inspection", "calibration", "overhaul"])}',
                scheduled_date=sched_date,
                estimated_duration_hours=random.uniform(1, 24),
                actual_duration_hours=random.uniform(1, 24) if mstatus == MaintenanceStatus.COMPLETED else None,
                started_at=sched_date if mstatus in [MaintenanceStatus.IN_PROGRESS, MaintenanceStatus.COMPLETED] else None,
                completed_at=sched_date + timedelta(hours=random.randint(1, 24)) if mstatus == MaintenanceStatus.COMPLETED else None,
                cost_estimate=random.uniform(500, 15000),
                actual_cost=random.uniform(500, 15000) if mstatus == MaintenanceStatus.COMPLETED else None,
                created_at=sched_date - timedelta(days=random.randint(1, 7)),
            )
            db.session.add(ms)

    print('Creating security incidents...')
    for i in range(400):
        detected = seven_years_ago + timedelta(days=random.randint(0, 2555), hours=random.randint(0, 23))
        status = random.choice([IncidentStatus.RESOLVED, IncidentStatus.CLOSED, IncidentStatus.ACTIVE, IncidentStatus.INVESTIGATING, IncidentStatus.FALSE_ALARM])
        resolved = detected + timedelta(hours=random.randint(1, 72)) if status in [IncidentStatus.RESOLVED, IncidentStatus.CLOSED] else None
        inc = SecurityIncident(
            incident_id=f'INC-{i+1:04d}',
            incident_type=random.choice(list(IncidentType)),
            zone=random.choice(list(SecurityZone)),
            severity=random.choice(list(IncidentSeverity)),
            status=status,
            title=random.choice([
                'Unauthorized access near gate', 'Suspicious vehicle detected', 'Perimeter breach alert',
                'Speed limit violation', 'Theft of equipment', 'Vandalism reported', 'Fire alarm triggered',
                'Hazmat spill detected', 'Access denied attempt', 'CCTV motion after hours'
            ]),
            description=f'Incident detected at {detected.strftime("%Y-%m-%d %H:%M")} in {random.choice(list(SecurityZone)).value}',
            location_details=f'Near {random.choice(["Gate 1", "Gate 2", "Berth 3", "Warehouse", "Yard Block A"])}',
            reported_by=random.choice(['CCTV System', 'Security Guard', 'Perimeter Sensor', 'Access Control', 'Manual Report']),
            camera_id=f'CAM-{random.randint(1, 20):02d}',
            detected_at=detected,
            acknowledged_at=detected + timedelta(minutes=random.randint(5, 60)) if status != IncidentStatus.ACTIVE else None,
            resolved_at=resolved,
            closed_at=resolved + timedelta(days=random.randint(1, 7)) if status == IncidentStatus.CLOSED else None,
            response_time_minutes=random.randint(5, 60),
            is_false_alarm=status == IncidentStatus.FALSE_ALARM,
        )
        db.session.add(inc)

    print('Creating alerts...')
    for i in range(250):
        created = seven_years_ago + timedelta(days=random.randint(0, 2555), hours=random.randint(0, 23))
        alert = Alert(
            alert_id=f'ALT-{i+1:04d}',
            alert_type=random.choice(list(AlertType)),
            title=random.choice([
                'High PM2.5 levels detected', 'Unauthorized access attempt', 'Equipment failure warning',
                'Fire alarm in warehouse', 'Gas leak detected', 'Severe weather warning',
                'Container temperature anomaly', 'Gate access violation', 'CCTV offline alert',
                'Truck over-speed detected'
            ]),
            message=f'Automated alert generated at {created.strftime("%Y-%m-%d %H:%M")}',
            zone=random.choice(list(SecurityZone)),
            camera_id=f'CAM-{random.randint(1, 20):02d}' if random.random() < 0.5 else None,
            severity=random.choice(list(IncidentSeverity)),
            is_read=random.random() < 0.7,
            is_acknowledged=random.random() < 0.5,
            acknowledged_at=created + timedelta(minutes=random.randint(5, 120)) if random.random() < 0.5 else None,
            created_at=created,
        )
        db.session.add(alert)

    print('Creating event logs...')
    event_types = list(EventType)
    severities = list(EventSeverity)
    event_descriptions = {
        EventType.SHIP_ARRIVAL: ['{name} arrived at {berth}', 'Vessel {name} checked in at Port'],
        EventType.SHIP_DEPARTURE: ['{name} departed from {berth}', 'Vessel {name} cleared port'],
        EventType.BERTH_ASSIGNMENT: ['{name} assigned to {berth}', 'Berth allocated for {name}'],
        EventType.BERTH_RELEASE: ['{name} released from {berth}', 'Berth {berth} now available'],
        EventType.CONTAINER_GATE_IN: ['Container {cid} entered via Gate {g}', 'Gate in recorded for {cid}'],
        EventType.CONTAINER_GATE_OUT: ['Container {cid} exited via Gate {g}', 'Gate out recorded for {cid}'],
        EventType.TRUCK_GATE_IN: ['Truck {truck} entered port', 'Gate in: {truck} at Gate {g}'],
        EventType.TRUCK_GATE_OUT: ['Truck {truck} exited port', 'Gate out: {truck} at Gate {g}'],
        EventType.SECURITY_INCIDENT: ['Security alert: {title}', 'Incident reported: {title}'],
        EventType.INVOICE_CREATED: ['Invoice {inv} created', 'Billing generated for {name}'],
        EventType.INVOICE_PAID: ['Invoice {inv} payment received', 'Payment recorded for {inv}'],
        EventType.USER_LOGIN: ['User {email} logged in', 'Session started for {email}'],
        EventType.SYSTEM: ['System {action}', 'Automated task: {action}'],
    }
    for i in range(4000):
        evt_type = random.choice(event_types)
        ts = seven_years_ago + timedelta(days=random.randint(0, 2555), hours=random.randint(0, 23), minutes=random.randint(0, 59))
        desc_templates = event_descriptions.get(evt_type, ['System event occurred'])
        desc = random.choice(desc_templates).format(
            name=random.choice(ship_names) if ships else 'Vessel',
            berth=f'Berth {random.randint(1, 9)}',
            cid=f'CONT-{random.randint(1, 1500):06d}',
            truck=f'TN-{random.randint(1000, 1600)}',
            g=random.randint(1, 2),
            title=random.choice(['Unauthorized access', 'Speed violation', 'Fire alarm', 'Equipment fault']),
            inv=f'INV-{random.randint(2020001, 2026400)}',
            email=random.choice(['superadmin@smartport.gov.in', 'admin@smartport.gov.in', 'portstaff@smartport.gov.in']),
            action=random.choice(['backup completed', 'report generated', 'data sync', 'health check'])
        )
        event = EventLog(
            event_type=evt_type,
            severity=random.choice(severities),
            entity_type=random.choice(['ship', 'container', 'truck', 'berth', 'invoice', 'user', 'security']),
            entity_id=str(random.randint(1, 500)),
            title=desc[:255],
            description=desc,
            user_id=random.choice(user_ids) if user_ids and random.random() < 0.8 else None,
            ip_address=f'192.168.1.{random.randint(1, 254)}',
            created_at=ts,
        )
        db.session.add(event)

    print('Creating invoices...')
    for i in range(500):
        ship = random.choice(ships) if ships else None
        berth = random.choice(berths) if berths else None
        period_start = seven_years_ago + timedelta(days=random.randint(0, 2500))
        period_end = period_start + timedelta(days=random.randint(7, 30))
        due = period_end + timedelta(days=random.randint(7, 30))
        status = random.choice([InvoiceStatus.PAID, InvoiceStatus.PAID, InvoiceStatus.SENT, InvoiceStatus.OVERDUE, InvoiceStatus.DRAFT])
        payment_method = random.choice(list(PaymentMethod)) if status == InvoiceStatus.PAID else None
        payment_date = due - timedelta(days=random.randint(1, 10)) if status == InvoiceStatus.PAID else None
        inv = Invoice(
            invoice_number=f'INV-{period_start.strftime("%Y%m")}-{i+1:04d}',
            ship_id=ship.id if ship else None,
            ship_name=ship.name if ship else 'Unknown Vessel',
            berth_id=berth.id if berth else None,
            berth_name=berth.name if berth else 'Unknown Berth',
            billing_period_start=period_start,
            billing_period_end=period_end,
            tax_rate=random.choice([0, 5, 12, 18]),
            discount=random.choice([0, 0, 0, random.uniform(100, 500)]),
            status=status,
            payment_status='Paid' if status == InvoiceStatus.PAID else 'Unpaid',
            payment_method=payment_method,
            payment_date=payment_date,
            payment_reference=f'REF{random.randint(100000, 999999)}' if payment_date else None,
            due_date=due,
            notes=random.choice(['Monthly berth invoice', 'Pilotage charges', 'Tugging services', 'Mooring fees', 'Storage charges']),
            terms='Payment due within 30 days.',
            issued_by=random.choice(user_ids) if user_ids else 1,
            created_at=period_end,
        )
        db.session.add(inv)
        db.session.flush()

        for _ in range(random.randint(2, 6)):
            cat = random.choice(list(BillingCategory))
            line = BillingLine(
                invoice_id=inv.id,
                category=cat,
                description=cat.value,
                quantity=random.uniform(1, 10),
                unit=random.choice(['day', 'hour', 'trip', 'unit']),
                unit_price=random.uniform(100, 5000),
                amount=random.uniform(100, 5000),
                created_at=period_end,
            )
            db.session.add(line)
        db.session.flush()
        inv.calculate_totals()
        # calculate_totals() derives balance_due from amount_paid, but that
        # defaults to 0 -- an invoice already marked PAID (with a real
        # payment_method/payment_date above) needs amount_paid actually set,
        # or "collected" totals and per-invoice balances stay wrong (every
        # "paid" invoice would still show its full amount as outstanding).
        if status == InvoiceStatus.PAID:
            inv.amount_paid = inv.total_amount
            inv.balance_due = 0

    print('Creating environmental readings (noise + water quality -- weather and air quality')
    print('come from real historical data via datasets/scripts/import_to_database.py)...')
    stations = MonitoringStation.query.all()
    station_ids = [s.id for s in stations]
    for sid in station_ids:
        current = seven_years_ago
        while current <= now:
            if random.random() < 0.3:
                n = NoiseReading(
                    station_id=sid,
                    leq=random.uniform(55, 95),
                    lmax=random.uniform(70, 120),
                    lmin=random.uniform(40, 70),
                    l10=random.uniform(65, 100),
                    l50=random.uniform(55, 85),
                    l90=random.uniform(45, 70),
                    ldn=random.uniform(60, 90),
                    cnel=random.uniform(65, 95),
                    recorded_at=current,
                )
                db.session.add(n)

            current += timedelta(days=1)

    # WaterQualityReading has no free real-time-monitoring public data
    # source (unlike weather/air quality via Open-Meteo), so -- like
    # NoiseReading above -- it's seeded with plausible synthetic values
    # rather than left at zero rows. Scoped to the actual water-quality
    # monitoring station (MS-002) rather than every station.
    water_stations = [s for s in stations if s.station_type == 'water_quality']
    for station in water_stations:
        current = seven_years_ago
        while current <= now:
            if random.random() < 0.3:
                wq = WaterQualityReading(
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
                )
                db.session.add(wq)

            current += timedelta(days=1)

    db.session.commit()
    print('Historical seed data created successfully.')
