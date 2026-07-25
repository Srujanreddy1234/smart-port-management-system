from datetime import datetime
from enum import Enum as PyEnum
from app.extensions import db
from sqlalchemy import Enum, Index, ForeignKey
from sqlalchemy.orm import relationship


class ContainerType(PyEnum):
    TWENTY_FT = '20ft'
    FORTY_FT = '40ft'
    FORTY_FT_HC = '40ft HC'
    REEFER = 'Reefer'
    HAZMAT = 'Hazmat'
    TANK = 'Tank'
    OPEN_TOP = 'Open Top'
    FLAT_RACK = 'Flat Rack'


class ContainerStatus(PyEnum):
    EMPTY = 'Empty'
    LOADED = 'Loaded'
    IN_TRANSIT = 'In Transit'
    AT_PORT = 'At Port'
    DELIVERED = 'Delivered'
    CUSTOMS_HOLD = 'Customs Hold'
    DAMAGED = 'Damaged'
    LOST = 'Lost'


class Container(db.Model):
    __tablename__ = 'containers'

    id = db.Column(db.Integer, primary_key=True)
    container_id = db.Column(db.String(50), unique=True, nullable=False, index=True)
    iso_code = db.Column(db.String(10))
    container_type = db.Column(Enum(ContainerType), nullable=False, index=True)
    status = db.Column(Enum(ContainerStatus), default=ContainerStatus.EMPTY, nullable=False, index=True)
    weight = db.Column(db.Float)
    max_weight = db.Column(db.Float)
    owner = db.Column(db.String(255), index=True)
    owner_code = db.Column(db.String(10), index=True)
    ship_id = db.Column(db.Integer, ForeignKey('ships.id'), index=True)
    truck_id = db.Column(db.Integer, ForeignKey('trucks.id'), index=True)
    origin_port = db.Column(db.String(100), index=True)
    destination_port = db.Column(db.String(100), index=True)
    current_location = db.Column(db.String(255), index=True)
    bay = db.Column(db.String(20), index=True)
    row = db.Column(db.String(20), index=True)
    tier = db.Column(db.String(20), index=True)
    seal_number = db.Column(db.String(50))
    seal_status = db.Column(db.String(20))
    temperature = db.Column(db.Float)
    humidity = db.Column(db.Float)
    is_reefer = db.Column(db.Boolean, default=False, index=True)
    is_hazardous = db.Column(db.Boolean, default=False, index=True)
    hazardous_class = db.Column(db.String(10))
    un_number = db.Column(db.String(20))
    customs_status = db.Column(db.String(50), index=True)
    loaded_at = db.Column(db.DateTime, index=True)
    gate_in_at = db.Column(db.DateTime, index=True)
    gate_out_at = db.Column(db.DateTime, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    ship = relationship('Ship', backref='containers')
    truck = relationship('Truck', backref='containers')

    __table_args__ = (
        Index('ix_container_ship_status', 'ship_id', 'status'),
        Index('ix_container_location_type', 'current_location', 'container_type'),
        Index('ix_container_dates_status', 'gate_in_at', 'gate_out_at', 'status'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'container_id': self.container_id,
            'iso_code': self.iso_code,
            'container_type': self.container_type.value,
            'status': self.status.value,
            'weight': self.weight,
            'max_weight': self.max_weight,
            'owner': self.owner,
            'owner_code': self.owner_code,
            'ship_id': self.ship_id,
            'truck_id': self.truck_id,
            'origin_port': self.origin_port,
            'destination_port': self.destination_port,
            'current_location': self.current_location,
            'bay': self.bay,
            'row': self.row,
            'tier': self.tier,
            'seal_number': self.seal_number,
            'seal_status': self.seal_status,
            'temperature': self.temperature,
            'humidity': self.humidity,
            'is_reefer': self.is_reefer,
            'is_hazardous': self.is_hazardous,
            'hazardous_class': self.hazardous_class,
            'un_number': self.un_number,
            'customs_status': self.customs_status,
            'loaded_at': self.loaded_at.isoformat() if self.loaded_at else None,
            'gate_in_at': self.gate_in_at.isoformat() if self.gate_in_at else None,
            'gate_out_at': self.gate_out_at.isoformat() if self.gate_out_at else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

    def __repr__(self):
        return f'<Container {self.container_id}>'


class ContainerHistory(db.Model):
    __tablename__ = 'container_history'

    id = db.Column(db.Integer, primary_key=True)
    container_id = db.Column(db.Integer, ForeignKey('containers.id'), nullable=False, index=True)
    event_type = db.Column(db.String(50), nullable=False)
    location = db.Column(db.String(255))
    description = db.Column(db.Text)
    performed_by = db.Column(db.String(255))
    history_metadata = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    container = relationship('Container', backref='history')

    __table_args__ = (
        Index('ix_container_history_container_date', 'container_id', 'created_at'),
        Index('ix_container_history_event_type', 'event_type'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'container_id': self.container_id,
            'event_type': self.event_type,
            'location': self.location,
            'description': self.description,
            'performed_by': self.performed_by,
            'metadata': self.history_metadata,
            'created_at': self.created_at.isoformat()
        }