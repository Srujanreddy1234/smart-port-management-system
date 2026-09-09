from datetime import datetime
from enum import Enum as PyEnum
from app.extensions import db
from sqlalchemy import Enum, Index, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship


class VesselType(PyEnum):
    CONTAINER_SHIP = 'Container Ship'
    BULK_CARRIER = 'Bulk Carrier'
    TANKER = 'Tanker'
    RO_RO = 'Ro-Ro'
    GENERAL_CARGO = 'General Cargo'
    FISHING = 'Fishing Vessel'
    TUG = 'Tug Boat'
    PILOT_BOAT = 'Pilot Boat'
    BARGE = 'Barge'
    OTHER = 'Other'


class ShipStatus(PyEnum):
    SCHEDULED = 'Scheduled'
    APPROACHING = 'Approaching'
    IN_CHANNEL = 'In Channel'
    ANCHORED = 'Anchored'
    AT_BERTH = 'At Berth'
    LOADING = 'Loading'
    UNLOADING = 'Unloading'
    DEPARTING = 'Departing'
    DEPARTED = 'Departed'
    DIVERTED = 'Diverted'
    DELAYED = 'Delayed'


class BerthStatus(PyEnum):
    AVAILABLE = 'Available'
    OCCUPIED = 'Occupied'
    MAINTENANCE = 'Maintenance'
    RESERVED = 'Reserved'
    OUT_OF_SERVICE = 'Out of Service'


class Ship(db.Model):
    __tablename__ = 'ships'

    id = db.Column(db.Integer, primary_key=True)
    ship_id = db.Column(db.String(50), unique=True, nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False, index=True)
    vessel_type = db.Column(Enum(VesselType, values_callable=lambda x: x.value), nullable=False, index=True)
    flag = db.Column(db.String(100), nullable=False)
    imo_number = db.Column(db.String(20), unique=True, index=True)
    mmsi = db.Column(db.String(20), unique=True, index=True)
    call_sign = db.Column(db.String(20))
    length_overall = db.Column(db.Float)
    beam = db.Column(db.Float)
    draft = db.Column(db.Float)
    gross_tonnage = db.Column(db.Integer)
    deadweight_tonnage = db.Column(db.Integer)
    max_containers = db.Column(db.Integer)
    status = db.Column(Enum(ShipStatus, values_callable=lambda x: x.value), default=ShipStatus.SCHEDULED, nullable=False, index=True)
    current_berth = db.Column(db.String(50), index=True)
    eta = db.Column(db.DateTime, index=True)
    etd = db.Column(db.DateTime, index=True)
    ata = db.Column(db.DateTime)
    atd = db.Column(db.DateTime)
    agent = db.Column(db.String(255))
    agent_contact = db.Column(db.String(255))
    agent_email = db.Column(db.String(255))
    cargo_description = db.Column(db.Text)
    containers_onboard = db.Column(db.Integer, default=0)
    containers_to_load = db.Column(db.Integer, default=0)
    containers_to_discharge = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index('ix_ship_status_berth', 'status', 'current_berth'),
        Index('ix_ship_eta_status', 'eta', 'status'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'ship_id': self.ship_id,
            'name': self.name,
            'vessel_type': self.vessel_type.value,
            'flag': self.flag,
            'imo_number': self.imo_number,
            'mmsi': self.mmsi,
            'call_sign': self.call_sign,
            'length_overall': self.length_overall,
            'beam': self.beam,
            'draft': self.draft,
            'gross_tonnage': self.gross_tonnage,
            'deadweight_tonnage': self.deadweight_tonnage,
            'max_containers': self.max_containers,
            'status': self.status.value,
            'current_berth': self.current_berth,
            'eta': self.eta.isoformat() if self.eta else None,
            'etd': self.etd.isoformat() if self.etd else None,
            'ata': self.ata.isoformat() if self.ata else None,
            'atd': self.atd.isoformat() if self.atd else None,
            'agent': self.agent,
            'agent_contact': self.agent_contact,
            'agent_email': self.agent_email,
            'cargo_description': self.cargo_description,
            'containers_onboard': self.containers_onboard,
            'containers_to_load': self.containers_to_load,
            'containers_to_discharge': self.containers_to_discharge,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

    def __repr__(self):
        return f'<Ship {self.name} ({self.ship_id})>'


class Berth(db.Model):
    __tablename__ = 'berths'

    id = db.Column(db.Integer, primary_key=True)
    berth_id = db.Column(db.String(50), unique=True, nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False, index=True)
    status = db.Column(Enum(BerthStatus, values_callable=lambda x: x.value), default=BerthStatus.AVAILABLE, nullable=False, index=True)
    max_length = db.Column(db.Float)
    max_beam = db.Column(db.Float)
    max_draft = db.Column(db.Float)
    max_tonnage = db.Column(db.Integer)
    max_containers = db.Column(db.Integer)
    depth = db.Column(db.Float)
    length = db.Column(db.Float)
    has_crane = db.Column(db.Boolean, default=False)
    crane_capacity = db.Column(db.Integer)
    has_reins = db.Column(db.Boolean, default=False)
    has_power = db.Column(db.Boolean, default=True)
    has_water = db.Column(db.Boolean, default=True)
    zone = db.Column(db.String(100), index=True)
    terminal = db.Column(db.String(100), index=True)
    notes = db.Column(db.Text)
    current_ship_id = db.Column(db.Integer, ForeignKey('ships.id'), index=True)
    occupied_since = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    current_ship = relationship('Ship', foreign_keys=[current_ship_id], backref='assigned_berth')

    __table_args__ = (
        Index('ix_berth_status_zone', 'status', 'zone'),
        Index('ix_berth_ship', 'current_ship_id'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'berth_id': self.berth_id,
            'name': self.name,
            'code': self.code,
            'status': self.status.value,
            'max_length': self.max_length,
            'max_beam': self.max_beam,
            'max_draft': self.max_draft,
            'max_tonnage': self.max_tonnage,
            'max_containers': self.max_containers,
            'depth': self.depth,
            'length': self.length,
            'has_crane': self.has_crane,
            'crane_capacity': self.crane_capacity,
            'has_reins': self.has_reins,
            'has_power': self.has_power,
            'has_water': self.has_water,
            'zone': self.zone,
            'terminal': self.terminal,
            'notes': self.notes,
            'current_ship_id': self.current_ship_id,
            'occupied_since': self.occupied_since.isoformat() if self.occupied_since else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

    def can_accommodate(self, ship):
        if self.status not in [BerthStatus.AVAILABLE, BerthStatus.RESERVED]:
            return False, 'Berth not available'
        if ship.length_overall and self.max_length and ship.length_overall > self.max_length:
            return False, f'Ship length ({ship.length_overall}m) exceeds berth max length ({self.max_length}m)'
        if ship.beam and self.max_beam and ship.beam > self.max_beam:
            return False, f'Ship beam ({ship.beam}m) exceeds berth max beam ({self.max_beam}m)'
        if ship.draft and self.max_draft and ship.draft > self.max_draft:
            return False, f'Ship draft ({ship.draft}m) exceeds berth max draft ({self.max_draft}m)'
        if ship.gross_tonnage and self.max_tonnage and ship.gross_tonnage > self.max_tonnage:
            return False, f'Ship tonnage ({ship.gross_tonnage}) exceeds berth max tonnage ({self.max_tonnage})'
        return True, 'Can accommodate'

    def __repr__(self):
        return f'<Berth {self.name} ({self.code})>'