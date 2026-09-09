from datetime import datetime
from enum import Enum as PyEnum
from app.extensions import db
from sqlalchemy import Enum, Index


class EquipmentType(PyEnum):
    CRANE_STS = 'Ship-to-Shore Crane'
    CRANE_RTG = 'RTG Crane'
    CRANE_RMG = 'RMG Crane'
    CRANE_MHC = 'Mobile Harbor Crane'
    REACH_STACKER = 'Reach Stacker'
    EMPTY_HANDLER = 'Empty Handler'
    FORKLIFT = 'Forklift'
    TOP_LOADER = 'Top Loader'
    SIDE_LOADER = 'Side Loader'
    CONVEYOR = 'Conveyor'
    AGV = 'AGV'
    STRADDLE_CARRIER = 'Straddle Carrier'
    TERMINAL_TRACTOR = 'Terminal Tractor'
    CHASSIS = 'Chassis'
    GENERATOR = 'Generator'
    PUMP = 'Pump'
    COMPRESSOR = 'Compressor'
    HVAC = 'HVAC System'
    OTHER = 'Other'


class EquipmentStatus(PyEnum):
    OPERATIONAL = 'Operational'
    MAINTENANCE = 'Maintenance'
    SCHEDULED = 'Scheduled'
    OUT_OF_SERVICE = 'Out of Service'
    DECOMMISSIONED = 'Decommissioned'
    STANDBY = 'Standby'


class MaintenanceType(PyEnum):
    PREVENTIVE = 'Preventive'
    CORRECTIVE = 'Corrective'
    PREDICTIVE = 'Predictive'
    EMERGENCY = 'Emergency'
    OVERHAUL = 'Overhaul'
    INSPECTION = 'Inspection'
    CALIBRATION = 'Calibration'


class MaintenancePriority(PyEnum):
    LOW = 'Low'
    MEDIUM = 'Medium'
    HIGH = 'High'
    CRITICAL = 'Critical'


class MaintenanceStatus(PyEnum):
    SCHEDULED = 'Scheduled'
    IN_PROGRESS = 'In Progress'
    ON_HOLD = 'On Hold'
    COMPLETED = 'Completed'
    CANCELLED = 'Cancelled'
    OVERDUE = 'Overdue'


class Equipment(db.Model):
    __tablename__ = 'equipment'

    id = db.Column(db.Integer, primary_key=True)
    equipment_id = db.Column(db.String(50), unique=True, nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    equipment_type = db.Column(Enum(EquipmentType, values_callable=lambda enum_cls: [e.value for e in enum_cls]), nullable=False, index=True)
    manufacturer = db.Column(db.String(255))
    model = db.Column(db.String(255))
    serial_number = db.Column(db.String(255), unique=True, index=True)
    year_manufactured = db.Column(db.Integer)
    location = db.Column(db.String(255), index=True)
    zone = db.Column(db.String(100), index=True)
    status = db.Column(Enum(EquipmentStatus, values_callable=lambda enum_cls: [e.value for e in enum_cls]), default=EquipmentStatus.OPERATIONAL, nullable=False, index=True)
    health_percentage = db.Column(db.Integer, default=100)
    operating_hours = db.Column(db.Float, default=0)
    last_service_date = db.Column(db.DateTime, index=True)
    next_service_date = db.Column(db.DateTime, index=True)
    last_inspection_date = db.Column(db.DateTime)
    next_inspection_date = db.Column(db.DateTime)
    warranty_expiry = db.Column(db.DateTime)
    specifications = db.Column(db.JSON)
    maintenance_interval_hours = db.Column(db.Float)
    inspection_interval_days = db.Column(db.Integer)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index('ix_equipment_status_location', 'status', 'location'),
        Index('ix_equipment_type_status', 'equipment_type', 'status'),
        Index('ix_equipment_next_service', 'next_service_date'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'equipment_id': self.equipment_id,
            'name': self.name,
            'equipment_type': self.equipment_type.value,
            'manufacturer': self.manufacturer,
            'model': self.model,
            'serial_number': self.serial_number,
            'year_manufactured': self.year_manufactured,
            'location': self.location,
            'zone': self.zone,
            'status': self.status.value,
            'health_percentage': self.health_percentage,
            'operating_hours': self.operating_hours,
            'last_service_date': self.last_service_date.isoformat() if self.last_service_date else None,
            'next_service_date': self.next_service_date.isoformat() if self.next_service_date else None,
            'last_inspection_date': self.last_inspection_date.isoformat() if self.last_inspection_date else None,
            'next_inspection_date': self.next_inspection_date.isoformat() if self.next_inspection_date else None,
            'warranty_expiry': self.warranty_expiry.isoformat() if self.warranty_expiry else None,
            'specifications': self.specifications,
            'maintenance_interval_hours': self.maintenance_interval_hours,
            'inspection_interval_days': self.inspection_interval_days,
            'notes': self.notes,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class MaintenanceSchedule(db.Model):
    __tablename__ = 'maintenance_schedules'

    id = db.Column(db.Integer, primary_key=True)
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment.id'), nullable=False, index=True)
    maintenance_type = db.Column(Enum(MaintenanceType, values_callable=lambda enum_cls: [e.value for e in enum_cls]), nullable=False, index=True)
    priority = db.Column(Enum(MaintenancePriority, values_callable=lambda enum_cls: [e.value for e in enum_cls]), default=MaintenancePriority.MEDIUM, nullable=False, index=True)
    status = db.Column(Enum(MaintenanceStatus, values_callable=lambda enum_cls: [e.value for e in enum_cls]), default=MaintenanceStatus.SCHEDULED, nullable=False, index=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    scheduled_date = db.Column(db.DateTime, nullable=False, index=True)
    estimated_duration_hours = db.Column(db.Float)
    actual_duration_hours = db.Column(db.Float)
    assigned_technician_id = db.Column(db.Integer, db.ForeignKey('users.id'), index=True)
    supervisor_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    cost_estimate = db.Column(db.Float)
    actual_cost = db.Column(db.Float)
    parts_used = db.Column(db.JSON)
    work_performed = db.Column(db.Text)
    findings = db.Column(db.Text)
    recommendations = db.Column(db.Text)
    next_maintenance_date = db.Column(db.DateTime)
    next_maintenance_type = db.Column(Enum(MaintenanceType, values_callable=lambda enum_cls: [e.value for e in enum_cls]))
    is_recurring = db.Column(db.Boolean, default=False)
    recurrence_pattern = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    equipment = db.relationship('Equipment', backref='maintenance_schedules')
    assigned_technician = db.relationship('User', foreign_keys=[assigned_technician_id], backref='assigned_maintenance')
    supervisor = db.relationship('User', foreign_keys=[supervisor_id], backref='supervised_maintenance')

    __table_args__ = (
        Index('ix_maintenance_equipment_status', 'equipment_id', 'status'),
        Index('ix_maintenance_scheduled_status', 'scheduled_date', 'status'),
        Index('ix_maintenance_technician_status', 'assigned_technician_id', 'status'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'equipment_id': self.equipment_id,
            'maintenance_type': self.maintenance_type.value,
            'priority': self.priority.value,
            'status': self.status.value,
            'title': self.title,
            'description': self.description,
            'scheduled_date': self.scheduled_date.isoformat() if self.scheduled_date else None,
            'estimated_duration_hours': self.estimated_duration_hours,
            'actual_duration_hours': self.actual_duration_hours,
            'assigned_technician_id': self.assigned_technician_id,
            'supervisor_id': self.supervisor_id,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'cost_estimate': self.cost_estimate,
            'actual_cost': self.actual_cost,
            'parts_used': self.parts_used,
            'work_performed': self.work_performed,
            'findings': self.findings,
            'recommendations': self.recommendations,
            'next_maintenance_date': self.next_maintenance_date.isoformat() if self.next_maintenance_date else None,
            'next_maintenance_type': self.next_maintenance_type.value if self.next_maintenance_type else None,
            'is_recurring': self.is_recurring,
            'recurrence_pattern': self.recurrence_pattern,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class ServiceLog(db.Model):
    __tablename__ = 'service_logs'

    id = db.Column(db.Integer, primary_key=True)
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment.id'), nullable=False, index=True)
    maintenance_schedule_id = db.Column(db.Integer, db.ForeignKey('maintenance_schedules.id'), index=True)
    service_type = db.Column(Enum(MaintenanceType, values_callable=lambda enum_cls: [e.value for e in enum_cls]), nullable=False, index=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    performed_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), index=True)
    supervisor_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    started_at = db.Column(db.DateTime, nullable=False, index=True)
    completed_at = db.Column(db.DateTime, index=True)
    duration_hours = db.Column(db.Float)
    cost = db.Column(db.Float)
    parts_used = db.Column(db.JSON)
    labor_hours = db.Column(db.Float)
    findings = db.Column(db.Text)
    recommendations = db.Column(db.Text)
    next_service_recommended = db.Column(db.DateTime)
    next_service_type = db.Column(Enum(MaintenanceType, values_callable=lambda enum_cls: [e.value for e in enum_cls]))
    meter_reading = db.Column(db.Float)
    meter_unit = db.Column(db.String(20))
    attachments = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    equipment = db.relationship('Equipment', backref='service_logs')
    maintenance_schedule = db.relationship('MaintenanceSchedule', backref='service_logs')
    performed_by = db.relationship('User', foreign_keys=[performed_by_id], backref='performed_services')
    supervisor = db.relationship('User', foreign_keys=[supervisor_id], backref='supervised_services')

    __table_args__ = (
        Index('ix_service_equipment_date', 'equipment_id', 'started_at'),
        Index('ix_service_type_date', 'service_type', 'started_at'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'equipment_id': self.equipment_id,
            'maintenance_schedule_id': self.maintenance_schedule_id,
            'service_type': self.service_type.value,
            'title': self.title,
            'description': self.description,
            'performed_by_id': self.performed_by_id,
            'supervisor_id': self.supervisor_id,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'duration_hours': self.duration_hours,
            'cost': self.cost,
            'parts_used': self.parts_used,
            'labor_hours': self.labor_hours,
            'findings': self.findings,
            'recommendations': self.recommendations,
            'next_service_recommended': self.next_service_recommended.isoformat() if self.next_service_recommended else None,
            'next_service_type': self.next_service_type.value if self.next_service_type else None,
            'meter_reading': self.meter_reading,
            'meter_unit': self.meter_unit,
            'attachments': self.attachments,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class EquipmentHealthLog(db.Model):
    __tablename__ = 'equipment_health_logs'

    id = db.Column(db.Integer, primary_key=True)
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment.id'), nullable=False, index=True)
    health_percentage = db.Column(db.Integer, nullable=False)
    vibration_level = db.Column(db.Float)
    temperature = db.Column(db.Float)
    pressure = db.Column(db.Float)
    oil_level = db.Column(db.Float)
    fuel_level = db.Column(db.Float)
    battery_voltage = db.Column(db.Float)
    operating_hours = db.Column(db.Float)
    load_percentage = db.Column(db.Float)
    error_codes = db.Column(db.JSON)
    sensor_data = db.Column(db.JSON)
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    recorded_by = db.Column(db.String(100))
    notes = db.Column(db.Text)

    equipment = db.relationship('Equipment', backref='health_logs')

    __table_args__ = (
        Index('ix_health_equipment_recorded', 'equipment_id', 'recorded_at'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'equipment_id': self.equipment_id,
            'health_percentage': self.health_percentage,
            'vibration_level': self.vibration_level,
            'temperature': self.temperature,
            'pressure': self.pressure,
            'oil_level': self.oil_level,
            'fuel_level': self.fuel_level,
            'battery_voltage': self.battery_voltage,
            'operating_hours': self.operating_hours,
            'load_percentage': self.load_percentage,
            'error_codes': self.error_codes,
            'sensor_data': self.sensor_data,
            'recorded_at': self.recorded_at.isoformat() if self.recorded_at else None,
            'recorded_by': self.recorded_by,
            'notes': self.notes
        }