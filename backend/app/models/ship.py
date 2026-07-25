from datetime import datetime
from enum import Enum as PyEnum
from app.extensions import db
from sqlalchemy import Enum, Index, ForeignKey
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


class Ship(db.Model):
    __tablename__ = 'ships'

    id = db.Column(db.Integer, primary_key=True)
    ship_id = db.Column(db.String(50), unique=True, nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False, index=True)
    vessel_type = db.Column(Enum(VesselType), nullable=False, index=True)
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
    status = db.Column(Enum(ShipStatus), default=ShipStatus.SCHEDULED, nullable=False, index=True)
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