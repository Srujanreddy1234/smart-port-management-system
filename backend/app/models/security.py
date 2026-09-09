from datetime import datetime
from enum import Enum as PyEnum
from app.extensions import db
from sqlalchemy import Enum, Index


class IncidentType(PyEnum):
    INTRUSION = 'Intrusion'
    PERIMETER_BREACH = 'Perimeter Breach'
    ACCESS_DENIED = 'Access Denied'
    SUSPICIOUS_ACTIVITY = 'Suspicious Activity'
    VIOLATION = 'Violation'
    THEFT = 'Theft'
    VANDALISM = 'Vandalism'
    FIRE = 'Fire'
    HAZMAT_INCIDENT = 'Hazmat Incident'
    OTHER = 'Other'


class IncidentSeverity(PyEnum):
    LOW = 'Low'
    MEDIUM = 'Medium'
    HIGH = 'High'
    CRITICAL = 'Critical'


class IncidentStatus(PyEnum):
    ACTIVE = 'Active'
    INVESTIGATING = 'Investigating'
    ESCALATED = 'Escalated'
    RESOLVED = 'Resolved'
    CLOSED = 'Closed'
    FALSE_ALARM = 'False Alarm'


class SecurityZone(PyEnum):
    ZONE_A = 'Zone A - Berth 1-3'
    ZONE_B = 'Zone B - Berth 4-6'
    ZONE_C = 'Zone C - Gate 1-2'
    ZONE_D = 'Zone D - Warehouse Row'
    ZONE_E = 'Zone E - Tank Farm'
    ZONE_F = 'Zone F - Admin Area'
    ZONE_G = 'Zone G - Cold Storage'
    ZONE_H = 'Zone H - Container Yard'


class SecurityIncident(db.Model):
    __tablename__ = 'security_incidents'

    id = db.Column(db.Integer, primary_key=True)
    incident_id = db.Column(db.String(50), unique=True, nullable=False, index=True)
    incident_type = db.Column(Enum(IncidentType, values_callable=lambda x: x.value), nullable=False, index=True)
    zone = db.Column(Enum(SecurityZone, values_callable=lambda x: x.value), nullable=False, index=True)
    severity = db.Column(Enum(IncidentSeverity, values_callable=lambda x: x.value), nullable=False, index=True)
    status = db.Column(Enum(IncidentStatus, values_callable=lambda x: x.value), default=IncidentStatus.ACTIVE, nullable=False, index=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    location_details = db.Column(db.String(500))
    reported_by = db.Column(db.String(255))
    assigned_officer_id = db.Column(db.Integer, db.ForeignKey('users.id'), index=True)
    camera_id = db.Column(db.String(50))
    camera_footage_url = db.Column(db.String(500))
    detected_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    acknowledged_at = db.Column(db.DateTime)
    resolved_at = db.Column(db.DateTime)
    closed_at = db.Column(db.DateTime)
    resolution_notes = db.Column(db.Text)
    response_time_minutes = db.Column(db.Integer)
    is_false_alarm = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    assigned_officer = db.relationship('User', foreign_keys=[assigned_officer_id], backref='assigned_incidents')

    __table_args__ = (
        Index('ix_incident_status_zone', 'status', 'zone'),
        Index('ix_incident_severity_detected', 'severity', 'detected_at'),
        Index('ix_incident_officer_status', 'assigned_officer_id', 'status'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'incident_id': self.incident_id,
            'incident_type': self.incident_type.value,
            'zone': self.zone.value,
            'severity': self.severity.value,
            'status': self.status.value,
            'title': self.title,
            'description': self.description,
            'location_details': self.location_details,
            'reported_by': self.reported_by,
            'assigned_officer_id': self.assigned_officer_id,
            'camera_id': self.camera_id,
            'camera_footage_url': self.camera_footage_url,
            'detected_at': self.detected_at.isoformat() if self.detected_at else None,
            'acknowledged_at': self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'closed_at': self.closed_at.isoformat() if self.closed_at else None,
            'resolution_notes': self.resolution_notes,
            'response_time_minutes': self.response_time_minutes,
            'is_false_alarm': self.is_false_alarm,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class AlertType(PyEnum):
    CAMERA_MOTION = 'Camera Motion Detection'
    PERIMETER_SENSOR = 'Perimeter Sensor'
    ACCESS_CONTROL = 'Access Control'
    FIRE_ALARM = 'Fire Alarm'
    GAS_DETECTION = 'Gas Detection'
    WEATHER = 'Weather Alert'
    EQUIPMENT = 'Equipment Alert'
    MANUAL = 'Manual Alert'


class Alert(db.Model):
    __tablename__ = 'alerts'

    id = db.Column(db.Integer, primary_key=True)
    alert_id = db.Column(db.String(50), unique=True, nullable=False, index=True)
    alert_type = db.Column(Enum(AlertType, values_callable=lambda x: x.value), nullable=False, index=True)
    title = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text)
    zone = db.Column(Enum(SecurityZone, values_callable=lambda x: x.value), index=True)
    camera_id = db.Column(db.String(50))
    severity = db.Column(Enum(IncidentSeverity, values_callable=lambda x: x.value), default=IncidentSeverity.MEDIUM, nullable=False, index=True)
    is_read = db.Column(db.Boolean, default=False, index=True)
    is_acknowledged = db.Column(db.Boolean, default=False, index=True)
    acknowledged_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), index=True)
    acknowledged_at = db.Column(db.DateTime)
    related_incident_id = db.Column(db.Integer, db.ForeignKey('security_incidents.id'), index=True)
    alert_metadata = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    acknowledged_by = db.relationship('User', foreign_keys=[acknowledged_by_id], backref='acknowledged_alerts')
    related_incident = db.relationship('SecurityIncident', foreign_keys=[related_incident_id], backref='alerts')

    __table_args__ = (
        Index('ix_alert_read_created', 'is_read', 'created_at'),
        Index('ix_alert_type_zone', 'alert_type', 'zone'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'alert_id': self.alert_id,
            'alert_type': self.alert_type.value,
            'title': self.title,
            'message': self.message,
            'zone': self.zone.value if self.zone else None,
            'camera_id': self.camera_id,
            'severity': self.severity.value,
            'is_read': self.is_read,
            'is_acknowledged': self.is_acknowledged,
            'acknowledged_by_id': self.acknowledged_by_id,
            'acknowledged_at': self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            'related_incident_id': self.related_incident_id,
            'metadata': self.alert_metadata,
            'created_at': self.created_at.isoformat()
        }


class Camera(db.Model):
    __tablename__ = 'cameras'

    id = db.Column(db.Integer, primary_key=True)
    camera_id = db.Column(db.String(50), unique=True, nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    zone = db.Column(Enum(SecurityZone, values_callable=lambda x: x.value), nullable=False, index=True)
    location = db.Column(db.String(500))
    ip_address = db.Column(db.String(50))
    stream_url = db.Column(db.String(500))
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_recording = db.Column(db.Boolean, default=False)
    last_motion_at = db.Column(db.DateTime)
    last_maintenance_at = db.Column(db.DateTime)
    camera_metadata = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index('ix_camera_zone_active', 'zone', 'is_active'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'camera_id': self.camera_id,
            'name': self.name,
            'zone': self.zone.value,
            'location': self.location,
            'ip_address': self.ip_address,
            'stream_url': self.stream_url,
            'is_active': self.is_active,
            'is_recording': self.is_recording,
            'last_motion_at': self.last_motion_at.isoformat() if self.last_motion_at else None,
            'last_maintenance_at': self.last_maintenance_at.isoformat() if self.last_maintenance_at else None,
            'metadata': self.camera_metadata,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class AccessLog(db.Model):
    __tablename__ = 'access_logs'

    id = db.Column(db.Integer, primary_key=True)
    person_id = db.Column(db.String(50), index=True)
    person_name = db.Column(db.String(255))
    zone = db.Column(Enum(SecurityZone, values_callable=lambda x: x.value), nullable=False, index=True)
    access_method = db.Column(db.String(50))
    status = db.Column(db.String(20), nullable=False, index=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    device_id = db.Column(db.String(50))
    access_metadata = db.Column(db.JSON)

    __table_args__ = (
        Index('ix_access_zone_timestamp', 'zone', 'timestamp'),
        Index('ix_access_person_timestamp', 'person_id', 'timestamp'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'person_id': self.person_id,
            'person_name': self.person_name,
            'zone': self.zone.value,
            'access_method': self.access_method,
            'status': self.status,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'device_id': self.device_id,
            'metadata': self.access_metadata
        }


class SecurityOfficer(db.Model):
    __tablename__ = 'security_officers'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    badge_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    shift = db.Column(db.String(50))
    station = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    radio_frequency = db.Column(db.String(50))
    is_on_duty = db.Column(db.Boolean, default=False)
    last_patrol_at = db.Column(db.DateTime)
    officer_metadata = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user = db.relationship('User', foreign_keys=[user_id], backref='security_officer_profile')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'badge_number': self.badge_number,
            'shift': self.shift,
            'station': self.station,
            'phone': self.phone,
            'radio_frequency': self.radio_frequency,
            'is_on_duty': self.is_on_duty,
            'last_patrol_at': self.last_patrol_at.isoformat() if self.last_patrol_at else None,
            'metadata': self.officer_metadata,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }