from datetime import datetime, timedelta
from enum import Enum as PyEnum
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db
from sqlalchemy import Enum, Index


class UserRole(PyEnum):
    SUPER_ADMIN = 'Super Admin'
    ADMIN = 'Admin'
    PORT_SUPERVISOR = 'Port Supervisor'
    PORT_STAFF = 'Port Staff'
    CUSTOMS_OFFICER = 'Customs Officer'
    SHIPPING_COMPANY = 'Shipping Company'
    TRUCK_OPERATOR = 'Truck Operator'
    CUSTOMER = 'Customer'
    PUBLIC = 'Public'


class UserStatus(PyEnum):
    ACTIVE = 'Active'
    INACTIVE = 'Inactive'
    SUSPENDED = 'Suspended'
    PENDING = 'Pending'


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    role = db.Column(Enum(UserRole), nullable=False, index=True)
    status = db.Column(Enum(UserStatus), default=UserStatus.ACTIVE, nullable=False, index=True)
    employee_id = db.Column(db.String(50), unique=True, index=True)
    department = db.Column(db.String(100), index=True)
    designation = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    mobile = db.Column(db.String(20))
    address = db.Column(db.Text)
    date_of_birth = db.Column(db.Date)
    date_of_joining = db.Column(db.Date)
    manager_id = db.Column(db.Integer, db.ForeignKey('users.id'), index=True)
    avatar_url = db.Column(db.String(500))
    last_login_at = db.Column(db.DateTime)
    last_login_ip = db.Column(db.String(45))
    failed_login_attempts = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime)
    password_changed_at = db.Column(db.DateTime)
    must_change_password = db.Column(db.Boolean, default=False)
    two_factor_enabled = db.Column(db.Boolean, default=False)
    two_factor_secret = db.Column(db.String(255))
    email_verified = db.Column(db.Boolean, default=False)
    email_verified_at = db.Column(db.DateTime)
    notification_preferences = db.Column(db.JSON)
    user_metadata = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    manager = db.relationship('User', remote_side=[id], backref='subordinates')

    __table_args__ = (
        Index('ix_user_role_status', 'role', 'status'),
        Index('ix_user_department_role', 'department', 'role'),
    )

    ROLE_PERMISSIONS = {
        UserRole.SUPER_ADMIN: [
            'all'
        ],
        UserRole.ADMIN: [
            'users.read', 'users.write', 'users.delete',
            'roles.read', 'roles.write', 'roles.delete',
            'ships.read', 'ships.write', 'ships.delete',
            'containers.read', 'containers.write', 'containers.delete',
            'trucks.read', 'trucks.write', 'trucks.delete',
            'berths.read', 'berths.write', 'berths.delete',
            'dashboard.read', 'dashboard.write',
            'reports.read', 'reports.write', 'reports.delete',
            'maintenance.read', 'maintenance.write', 'maintenance.delete',
            'security.read', 'security.write', 'security.delete',
            'environment.read', 'environment.write', 'environment.delete',
            'audit.read', 'settings.read', 'settings.write',
        ],
        UserRole.PORT_SUPERVISOR: [
            'ships.read', 'ships.write',
            'containers.read', 'containers.write',
            'trucks.read', 'trucks.write',
            'berths.read', 'berths.write',
            'dashboard.read', 'reports.read', 'reports.write',
            'maintenance.read', 'maintenance.write',
            'security.read', 'security.write',
            'environment.read',
            'audit.read',
        ],
        UserRole.PORT_STAFF: [
            'ships.read', 'ships.write',
            'containers.read', 'containers.write',
            'trucks.read', 'trucks.write',
            'berths.read',
            'dashboard.read', 'reports.read',
            'maintenance.read', 'maintenance.write',
            'security.read',
        ],
        UserRole.CUSTOMS_OFFICER: [
            'containers.read', 'containers.write',
            'trucks.read',
            'ships.read',
            'dashboard.read', 'reports.read',
            'security.read',
        ],
        UserRole.SHIPPING_COMPANY: [
            'ships.read',
            'containers.read', 'containers.write',
            'trucks.read',
            'dashboard.read', 'reports.read',
            'berths.read',
        ],
        UserRole.TRUCK_OPERATOR: [
            'trucks.read', 'trucks.write',
            'containers.read',
            'ships.read',
            'dashboard.read', 'reports.read',
        ],
        UserRole.CUSTOMER: [
            'containers.read',
            'ships.read',
            'dashboard.read', 'reports.read',
        ],
        UserRole.PUBLIC: [
            'ships.read',
            'dashboard.read',
        ],
    }

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')
        self.password_changed_at = datetime.utcnow()
        self.must_change_password = False

    def check_password(self, password):
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    def has_permission(self, permission):
        permissions = self.ROLE_PERMISSIONS.get(self.role, [])
        if 'all' in permissions:
            return True
        return permission in permissions

    def has_any_permission(self, permissions):
        return any(self.has_permission(p) for p in permissions)

    def has_all_permissions(self, permissions):
        return all(self.has_permission(p) for p in permissions)

    def can_access_module(self, module):
        module_permissions = {
            'dashboard': 'dashboard.read',
            'ships': 'ships.read',
            'containers': 'containers.read',
            'trucks': 'trucks.read',
            'berths': 'berths.read',
            'security': 'security.read',
            'maintenance': 'maintenance.read',
            'environment': 'environment.read',
            'reports': 'reports.read',
            'users': 'users.read',
            'roles': 'roles.read',
            'audit': 'audit.read',
            'settings': 'settings.read',
            'admin': 'all',
        }
        required = module_permissions.get(module)
        if not required:
            return True
        return self.has_permission(required)

    def is_active(self):
        return self.status == UserStatus.ACTIVE

    def is_locked(self):
        if self.locked_until:
            return datetime.utcnow() < self.locked_until
        return False

    def record_failed_login(self):
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= 5:
            self.locked_until = datetime.utcnow() + timedelta(minutes=15)

    def record_successful_login(self, ip=None):
        self.last_login_at = datetime.utcnow()
        self.last_login_ip = ip
        self.failed_login_attempts = 0
        self.locked_until = None

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    def get_initials(self):
        return f"{self.first_name[0]}{self.last_name[0]}".upper()

    def to_dict(self, include_sensitive=False):
        data = {
            'id': self.id,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.get_full_name(),
            'initials': self.get_initials(),
            'role': self.role.value,
            'status': self.status.value,
            'employee_id': self.employee_id,
            'department': self.department,
            'designation': self.designation,
            'phone': self.phone,
            'mobile': self.mobile,
            'avatar_url': self.avatar_url,
            'last_login_at': self.last_login_at.isoformat() if self.last_login_at else None,
            'last_login_ip': self.last_login_ip,
            'two_factor_enabled': self.two_factor_enabled,
            'email_verified': self.email_verified,
            'email_verified_at': self.email_verified_at.isoformat() if self.email_verified_at else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
        if include_sensitive:
            data['permissions'] = self.ROLE_PERMISSIONS.get(self.role, [])
        return data

    def to_list_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'full_name': self.get_full_name(),
            'role': self.role.value,
            'status': self.status.value,
            'employee_id': self.employee_id,
            'department': self.department,
            'designation': self.designation,
            'last_login_at': self.last_login_at.isoformat() if self.last_login_at else None,
            'created_at': self.created_at.isoformat()
        }

    def __repr__(self):
        return f'<User {self.email} ({self.role.value})>'


class Session(db.Model):
    __tablename__ = 'sessions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    token = db.Column(db.String(1024), unique=True, nullable=False, index=True)
    refresh_token = db.Column(db.String(1024), unique=True, index=True)
    user_agent = db.Column(db.String(500))
    ip_address = db.Column(db.String(45))
    device_info = db.Column(db.JSON)
    expires_at = db.Column(db.DateTime, nullable=False, index=True)
    refresh_expires_at = db.Column(db.DateTime, nullable=False)
    is_revoked = db.Column(db.Boolean, default=False, index=True)
    revoked_at = db.Column(db.DateTime)
    revoked_reason = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship('User', backref='sessions')

    __table_args__ = (
        Index('ix_session_user_expires', 'user_id', 'expires_at'),
        Index('ix_session_token_expires', 'token', 'expires_at'),
    )

    def is_valid(self):
        return not self.is_revoked and datetime.utcnow() < self.expires_at

    def is_refresh_valid(self):
        return not self.is_revoked and datetime.utcnow() < self.refresh_expires_at

    def revoke(self, reason=None):
        self.is_revoked = True
        self.revoked_at = datetime.utcnow()
        self.revoked_reason = reason

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'token': self.token,
            'user_agent': self.user_agent,
            'ip_address': self.ip_address,
            'device_info': self.device_info,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'is_revoked': self.is_revoked,
            'created_at': self.created_at.isoformat()
        }


class AuditLog(db.Model):
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), index=True)
    session_id = db.Column(db.Integer, db.ForeignKey('sessions.id'))
    action = db.Column(db.String(100), nullable=False, index=True)
    resource_type = db.Column(db.String(100), index=True)
    resource_id = db.Column(db.String(100), index=True)
    description = db.Column(db.Text)
    old_values = db.Column(db.JSON)
    new_values = db.Column(db.JSON)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(500))
    status = db.Column(db.String(20), default='success', index=True)
    error_message = db.Column(db.Text)
    duration_ms = db.Column(db.Integer)
    audit_metadata = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    user = db.relationship('User', backref='audit_logs')
    session = db.relationship('Session', backref='audit_logs')

    __table_args__ = (
        Index('ix_audit_user_action', 'user_id', 'action'),
        Index('ix_audit_resource', 'resource_type', 'resource_id'),
        Index('ix_audit_created_status', 'created_at', 'status'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'action': self.action,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'description': self.description,
            'old_values': self.old_values,
            'new_values': self.new_values,
            'ip_address': self.ip_address,
            'status': self.status,
            'error_message': self.error_message,
            'duration_ms': self.duration_ms,
            'metadata': self.audit_metadata,
            'created_at': self.created_at.isoformat()
        }


class Permission(db.Model):
    __tablename__ = 'permissions'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    description = db.Column(db.String(255))
    module = db.Column(db.String(50), nullable=False, index=True)
    action = db.Column(db.String(50), nullable=False)
    is_system = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'module': self.module,
            'action': self.action,
            'is_system': self.is_system,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

    def __repr__(self):
        return f'<Permission {self.name}>'


class Role(db.Model):
    __tablename__ = 'roles'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    display_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    is_system = db.Column(db.Boolean, default=False)
    permissions = db.relationship('Permission', secondary='role_permissions', backref='roles')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'display_name': self.display_name,
            'description': self.description,
            'is_system': self.is_system,
            'permissions': [p.to_dict() for p in self.permissions],
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

    def has_permission(self, permission_name):
        return any(p.name == permission_name for p in self.permissions)

    def __repr__(self):
        return f'<Role {self.name}>'


class RolePermission(db.Model):
    __tablename__ = 'role_permissions'

    id = db.Column(db.Integer, primary_key=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False, index=True)
    permission_id = db.Column(db.Integer, db.ForeignKey('permissions.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        db.UniqueConstraint('role_id', 'permission_id', name='uq_role_permission'),
    )