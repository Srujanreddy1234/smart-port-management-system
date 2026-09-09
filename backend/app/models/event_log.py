from datetime import datetime
from enum import Enum as PyEnum
from app.extensions import db
from sqlalchemy import Enum, Index


class EventType(PyEnum):
    SHIP_ARRIVAL = 'Ship Arrival'
    SHIP_DEPARTURE = 'Ship Departure'
    BERTH_ASSIGNMENT = 'Berth Assignment'
    BERTH_RELEASE = 'Berth Release'
    CONTAINER_GATE_IN = 'Container Gate In'
    CONTAINER_GATE_OUT = 'Container Gate Out'
    CONTAINER_MOVE = 'Container Move'
    TRUCK_GATE_IN = 'Truck Gate In'
    TRUCK_GATE_OUT = 'Truck Gate Out'
    SECURITY_INCIDENT = 'Security Incident'
    MAINTENANCE_ALERT = 'Maintenance Alert'
    ENVIRONMENTAL_ALERT = 'Environmental Alert'
    USER_LOGIN = 'User Login'
    USER_LOGOUT = 'User Logout'
    INVOICE_CREATED = 'Invoice Created'
    INVOICE_PAID = 'Invoice Paid'
    SYSTEM = 'System'


class EventSeverity(PyEnum):
    INFO = 'INFO'
    WARNING = 'WARNING'
    CRITICAL = 'CRITICAL'


class EventLog(db.Model):
    __tablename__ = 'event_logs'

    id = db.Column(db.Integer, primary_key=True)
    event_type = db.Column(Enum(EventType), nullable=False, index=True)
    severity = db.Column(Enum(EventSeverity), default=EventSeverity.INFO, nullable=False, index=True)
    entity_type = db.Column(db.String(50), index=True)
    entity_id = db.Column(db.String(50), index=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    event_data = db.Column(db.JSON)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), index=True)
    ip_address = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    user = db.relationship('User', backref='event_logs')

    __table_args__ = (
        Index('ix_event_type_created', 'event_type', 'created_at'),
        Index('ix_event_entity', 'entity_type', 'entity_id'),
        Index('ix_event_user_created', 'user_id', 'created_at'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'event_type': self.event_type.value,
            'severity': self.severity.value,
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
            'title': self.title,
            'description': self.description,
            'data': self.event_data,
            'user_id': self.user_id,
            'ip_address': self.ip_address,
            'created_at': self.created_at.isoformat()
        }

    @staticmethod
    def log(event_type, title, description=None, entity_type=None, entity_id=None,
            severity=None, user_id=None, ip_address=None, data=None):
        event = EventLog(
            event_type=event_type,
            severity=severity or EventSeverity.INFO,
            entity_type=entity_type,
            entity_id=str(entity_id) if entity_id else None,
            title=title,
            description=description,
            event_data=data,
            user_id=user_id,
            ip_address=ip_address,
        )
        db.session.add(event)
        db.session.flush()
        return event

    def __repr__(self):
        return f'<EventLog {self.event_type.value} - {self.title}>'
