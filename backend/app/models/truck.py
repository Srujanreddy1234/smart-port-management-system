from datetime import datetime
from enum import Enum as PyEnum
from app.extensions import db
from sqlalchemy import Enum, Index, ForeignKey
from sqlalchemy.orm import relationship


class TruckType(PyEnum):
    PRIME_MOVER = 'Prime Mover'
    TRAILER = 'Trailer'
    CHASSIS = 'Chassis'
    REACH_STACKER = 'Reach Stacker'
    FORKLIFT = 'Forklift'
    EMPTY_HANDLER = 'Empty Handler'
    OTHER = 'Other'


class TruckStatus(PyEnum):
    AVAILABLE = 'Available'
    ASSIGNED = 'Assigned'
    LOADING = 'Loading'
    UNLOADING = 'Unloading'
    IN_TRANSIT = 'In Transit'
    AT_GATE = 'At Gate'
    WAITING = 'Waiting'
    MAINTENANCE = 'Maintenance'
    OFFLINE = 'Offline'


class Truck(db.Model):
    __tablename__ = 'trucks'

    id = db.Column(db.Integer, primary_key=True)
    truck_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    driver_name = db.Column(db.String(255))
    driver_phone = db.Column(db.String(20))
    truck_type = db.Column(Enum(TruckType, values_callable=lambda x: x.value), nullable=False, index=True)
    status = db.Column(Enum(TruckStatus, values_callable=lambda x: x.value), default=TruckStatus.AVAILABLE, nullable=False, index=True)
    capacity = db.Column(db.Integer)
    license_plate = db.Column(db.String(50), unique=True, index=True)
    chassis_number = db.Column(db.String(50))
    owner = db.Column(db.String(255))
    owner_contact = db.Column(db.String(255))
    assigned_container_id = db.Column(db.Integer, ForeignKey('containers.id'), index=True)
    current_location = db.Column(db.String(255), index=True)
    gate_in_time = db.Column(db.DateTime, index=True)
    gate_out_time = db.Column(db.DateTime, index=True)
    assigned_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    assigned_container = relationship('Container', foreign_keys=[assigned_container_id], backref='assigned_truck')

    __table_args__ = (
        Index('ix_truck_status_location', 'status', 'current_location'),
        Index('ix_truck_type_status', 'truck_type', 'status'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'truck_number': self.truck_number,
            'driver_name': self.driver_name,
            'driver_phone': self.driver_phone,
            'truck_type': self.truck_type.value,
            'status': self.status.value,
            'capacity': self.capacity,
            'license_plate': self.license_plate,
            'chassis_number': self.chassis_number,
            'owner': self.owner,
            'owner_contact': self.owner_contact,
            'assigned_container_id': self.assigned_container_id,
            'current_location': self.current_location,
            'gate_in_time': self.gate_in_time.isoformat() if self.gate_in_time else None,
            'gate_out_time': self.gate_out_time.isoformat() if self.gate_out_time else None,
            'assigned_at': self.assigned_at.isoformat() if self.assigned_at else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

    def __repr__(self):
        return f'<Truck {self.truck_number}>'