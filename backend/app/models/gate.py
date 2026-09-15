from datetime import datetime
from enum import Enum as PyEnum
from app.extensions import db
from sqlalchemy import Enum, Index, ForeignKey
from sqlalchemy.orm import relationship


class GateStatus(PyEnum):
    OPEN = 'Open'
    CLOSED = 'Closed'
    MAINTENANCE = 'Maintenance'


class GateType(PyEnum):
    CONTAINER = 'Container Terminal'
    BULK_CARGO = 'Bulk Cargo'
    GENERAL = 'General / Mixed'
    TANKER = 'Tanker / Liquid Cargo'


class BookingStatus(PyEnum):
    BOOKED = 'Booked'
    CHECKED_IN = 'Checked In'
    COMPLETED = 'Completed'
    CANCELLED = 'Cancelled'
    NO_SHOW = 'No Show'


class BookingPurpose(PyEnum):
    CONTAINER_PICKUP = 'Container Pickup'
    CONTAINER_DELIVERY = 'Container Delivery'
    CARGO_PICKUP = 'Cargo Pickup'
    CARGO_DELIVERY = 'Cargo Delivery'
    EMPTY_RETURN = 'Empty Return'
    OTHER = 'Other'


class Gate(db.Model):
    """A physical truck entry/exit gate into the port. Congestion for a
    gate is derived at read time from live Truck.status/current_gate_id
    and near-term GateBooking density -- this table only stores the
    gate's static identity and configured hourly capacity, never a
    stored/cached congestion number that could go stale."""
    __tablename__ = 'gates'

    id = db.Column(db.Integer, primary_key=True)
    gate_code = db.Column(db.String(20), unique=True, nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    gate_type = db.Column(Enum(GateType, values_callable=lambda enum_cls: [e.value for e in enum_cls]), nullable=False, index=True)
    status = db.Column(Enum(GateStatus, values_callable=lambda enum_cls: [e.value for e in enum_cls]), default=GateStatus.OPEN, nullable=False, index=True)
    zone = db.Column(db.String(100))
    capacity_per_hour = db.Column(db.Integer, nullable=False, default=20)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    notes = db.Column(db.String(500))
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'gate_code': self.gate_code,
            'name': self.name,
            'gate_type': self.gate_type.value,
            'status': self.status.value,
            'zone': self.zone,
            'capacity_per_hour': self.capacity_per_hour,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'notes': self.notes,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }

    def __repr__(self):
        return f'<Gate {self.gate_code}>'


class GateBooking(db.Model):
    """A driver's reserved arrival time slot at a specific gate -- the
    core of a Truck Appointment System (TAS): spreading truck arrivals
    across the day instead of everyone converging on the gate at once,
    which is the standard, proven approach terminals use to cut queueing
    (documented turnaround-time reductions of ~30% in industry studies)."""
    __tablename__ = 'gate_bookings'

    id = db.Column(db.Integer, primary_key=True)
    gate_id = db.Column(db.Integer, ForeignKey('gates.id'), nullable=False, index=True)
    truck_id = db.Column(db.Integer, ForeignKey('trucks.id'), index=True)
    booked_by_user_id = db.Column(db.Integer, ForeignKey('users.id'), index=True)
    driver_name = db.Column(db.String(255))
    driver_phone = db.Column(db.String(20))
    truck_number = db.Column(db.String(50))
    purpose = db.Column(Enum(BookingPurpose, values_callable=lambda enum_cls: [e.value for e in enum_cls]), nullable=False)
    container_id = db.Column(db.Integer, ForeignKey('containers.id'), index=True)
    slot_start = db.Column(db.DateTime, nullable=False, index=True)
    slot_end = db.Column(db.DateTime, nullable=False)
    status = db.Column(Enum(BookingStatus, values_callable=lambda enum_cls: [e.value for e in enum_cls]), default=BookingStatus.BOOKED, nullable=False, index=True)
    checked_in_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    notes = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    gate = relationship('Gate', foreign_keys=[gate_id], backref='bookings')
    truck = relationship('Truck', foreign_keys=[truck_id])
    container = relationship('Container', foreign_keys=[container_id])
    booked_by = relationship('User', foreign_keys=[booked_by_user_id])

    __table_args__ = (
        Index('ix_gate_booking_slot', 'gate_id', 'slot_start'),
        Index('ix_gate_booking_status_slot', 'status', 'slot_start'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'gate_id': self.gate_id,
            'gate': self.gate.to_dict() if self.gate else None,
            'truck_id': self.truck_id,
            'booked_by_user_id': self.booked_by_user_id,
            'driver_name': self.driver_name,
            'driver_phone': self.driver_phone,
            'truck_number': self.truck_number,
            'purpose': self.purpose.value,
            'container_id': self.container_id,
            'slot_start': self.slot_start.isoformat(),
            'slot_end': self.slot_end.isoformat(),
            'status': self.status.value,
            'checked_in_at': self.checked_in_at.isoformat() if self.checked_in_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'notes': self.notes,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }

    def __repr__(self):
        return f'<GateBooking {self.id} gate={self.gate_id} slot={self.slot_start}>'
