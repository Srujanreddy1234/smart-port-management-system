from datetime import datetime, timedelta
import secrets
from flask import current_app, request
from flask_jwt_extended import (
    create_access_token, create_refresh_token, get_jwt_identity,
    get_jwt, decode_token
)
from app.extensions import db, bcrypt
from app.models.user import User, Session, AuditLog, UserRole, UserStatus
from app.utils.exceptions import ValidationError, AuthenticationError, AuthorizationError, NotFoundError


class AuthService:
    @staticmethod
    def register(data, current_user=None):
        if User.query.filter_by(email=data['email'].lower()).first():
            raise ValidationError('Email already registered')

        if current_user and not current_user.has_permission('users.write'):
            raise AuthorizationError('Insufficient permissions to create users')

        user = User(
            email=data['email'].lower(),
            first_name=data['first_name'],
            last_name=data['last_name'],
            role=UserRole(data.get('role', 'viewer')),
            status=UserStatus(data.get('status', 'active')),
            employee_id=data.get('employee_id'),
            department=data.get('department'),
            designation=data.get('designation'),
            phone=data.get('phone'),
            mobile=data.get('mobile'),
            date_of_birth=data.get('date_of_birth'),
            date_of_joining=data.get('date_of_joining') or datetime.utcnow().date(),
        )
        user.set_password(data['password'])

        db.session.add(user)
        db.session.flush()

        AuthService._log_audit(
            user_id=current_user.id if current_user else user.id,
            action='user.create',
            resource_type='user',
            resource_id=str(user.id),
            description=f'Created user {user.email}',
            new_values=user.to_dict(),
            status='success'
        )

        db.session.commit()
        return user

    @staticmethod
    def login(email, password, remember_me=False):
        user = User.query.filter_by(email=email.lower()).first()

        if not user:
            AuthService._log_audit(
                user_id=None,
                action='auth.login_failed',
                resource_type='auth',
                description=f'Login attempt for non-existent email: {email}',
                status='failure',
                error_message='Invalid credentials'
            )
            raise AuthenticationError('Invalid credentials')

        if user.is_locked():
            AuthService._log_audit(
                user_id=user.id,
                action='auth.login_failed',
                resource_type='auth',
                description='Account locked due to failed attempts',
                status='failure',
                error_message='Account locked'
            )
            raise AuthenticationError('Account temporarily locked. Try again later.')

        if not user.check_password(password):
            user.record_failed_login()
            db.session.commit()

            AuthService._log_audit(
                user_id=user.id,
                action='auth.login_failed',
                resource_type='auth',
                description='Invalid password',
                status='failure',
                error_message='Invalid credentials'
            )
            raise AuthenticationError('Invalid credentials')

        if not user.is_active():
            raise AuthenticationError('Account is inactive')

        user.record_successful_login(request.remote_addr if request else None)

        access_token_expires = timedelta(days=30) if remember_me else timedelta(hours=2)
        access_token = create_access_token(
            identity=str(user.id),
            expires_delta=access_token_expires,
            additional_claims={
                'role': user.role.value,
                'permissions': User.ROLE_PERMISSIONS.get(user.role, [])
            }
        )
        refresh_token = create_refresh_token(identity=str(user.id))

        session = Session(
            user_id=user.id,
            token=secrets.token_urlsafe(32),
            refresh_token=refresh_token,
            user_agent=request.user_agent.string if request else None,
            ip_address=request.remote_addr if request else None,
            expires_at=datetime.utcnow() + access_token_expires,
            refresh_expires_at=datetime.utcnow() + timedelta(days=30)
        )
        db.session.add(session)

        AuthService._log_audit(
            user_id=user.id,
            action='auth.login',
            resource_type='auth',
            description='Successful login',
            status='success'
        )

        db.session.commit()

        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_type': 'Bearer',
            'expires_in': int(access_token_expires.total_seconds()),
            'user': user.to_dict()
        }

    @staticmethod
    def logout(token_jti=None):
        current_user_id = get_jwt_identity()
        if token_jti:
            session = Session.query.filter_by(token=token_jti).first()
        else:
            jwt_data = get_jwt()
            session = Session.query.filter_by(token=jwt_data.get('jti')).first()

        if session:
            session.revoke('User logout')
            db.session.commit()

        AuthService._log_audit(
            user_id=current_user_id,
            action='auth.logout',
            resource_type='auth',
            description='User logged out',
            status='success'
        )

        return {'message': 'Logged out successfully'}

    @staticmethod
    def refresh_token():
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)

        if not user or not user.is_active():
            raise AuthenticationError('User not found or inactive')

        access_token = create_access_token(
            identity=str(user.id),
            additional_claims={
                'role': user.role.value,
                'permissions': User.ROLE_PERMISSIONS.get(user.role, [])
            }
        )

        return {'access_token': access_token, 'token_type': 'Bearer'}

    @staticmethod
    def get_current_user():
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)

        if not user:
            raise NotFoundError('User not found')

        return user

    @staticmethod
    def update_profile(user_id, data, current_user):
        user = User.query.get(user_id)

        if not user:
            raise NotFoundError('User not found')

        if current_user.id != user_id and not current_user.has_permission('users.write'):
            raise AuthorizationError('Insufficient permissions')

        old_values = user.to_dict()

        for field in ['first_name', 'last_name', 'phone', 'mobile', 'avatar_url']:
            if field in data:
                setattr(user, field, data[field])

        if current_user.has_permission('users.write'):
            for field in ['role', 'status', 'employee_id', 'department', 'designation', 'two_factor_enabled']:
                if field in data:
                    if field == 'role':
                        setattr(user, field, UserRole(data[field]))
                    elif field == 'status':
                        setattr(user, field, UserStatus(data[field]))
                    else:
                        setattr(user, field, data[field])

        user.updated_at = datetime.utcnow()

        AuthService._log_audit(
            user_id=current_user.id,
            action='user.update',
            resource_type='user',
            resource_id=str(user.id),
            description=f'Updated user {user.email}',
            old_values=old_values,
            new_values=user.to_dict(),
            status='success'
        )

        db.session.commit()
        return user

    @staticmethod
    def change_password(user_id, data, current_user):
        user = User.query.get(user_id)

        if not user:
            raise NotFoundError('User not found')

        if current_user.id != user_id and not current_user.has_permission('users.write'):
            raise AuthorizationError('Insufficient permissions')

        if not user.check_password(data['current_password']):
            raise ValidationError('Current password is incorrect')

        user.set_password(data['new_password'])

        AuthService._log_audit(
            user_id=current_user.id,
            action='user.password_change',
            resource_type='user',
            resource_id=str(user.id),
            description=f'Password changed for {user.email}',
            status='success'
        )

        Session.query.filter_by(user_id=user.id, is_revoked=False).update({'is_revoked': True})

        db.session.commit()
        return {'message': 'Password changed successfully'}

    @staticmethod
    def list_users(query_params, current_user):
        if not current_user.has_permission('users.read'):
            raise AuthorizationError('Insufficient permissions')

        query = User.query

        if query_params.get('role'):
            query = query.filter(User.role == UserRole(query_params['role']))
        if query_params.get('status'):
            query = query.filter(User.status == UserStatus(query_params['status']))
        if query_params.get('department'):
            query = query.filter(User.department.ilike(f"%{query_params['department']}%"))
        if query_params.get('search'):
            search = f"%{query_params['search']}%"
            query = query.filter(
                db.or_(
                    User.email.ilike(search),
                    User.first_name.ilike(search),
                    User.last_name.ilike(search),
                    User.employee_id.ilike(search)
                )
            )

        sort_by = query_params.get('sort_by', 'created_at')
        sort_order = query_params.get('sort_order', 'desc')
        sort_column = getattr(User, sort_by, User.created_at)
        if sort_order == 'desc':
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

        page = query_params.get('page', 1)
        per_page = min(query_params.get('per_page', 20), 100)

        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        return {
            'items': [u.to_list_dict() for u in pagination.items],
            'total': pagination.total,
            'page': pagination.page,
            'per_page': pagination.per_page,
            'pages': pagination.pages,
            'has_next': pagination.has_next,
            'has_prev': pagination.has_prev
        }

    @staticmethod
    def get_user(user_id, current_user):
        if not current_user.has_permission('users.read'):
            raise AuthorizationError('Insufficient permissions')

        user = User.query.get(user_id)

        if not user:
            raise NotFoundError('User not found')

        return user

    @staticmethod
    def delete_user(user_id, current_user):
        if not current_user.has_permission('users.delete'):
            raise AuthorizationError('Insufficient permissions')

        user = User.query.get(user_id)

        if not user:
            raise NotFoundError('User not found')

        if user.id == current_user.id:
            raise ValidationError('Cannot delete your own account')

        AuthService._log_audit(
            user_id=current_user.id,
            action='user.delete',
            resource_type='user',
            resource_id=str(user.id),
            description=f'Deleted user {user.email}',
            old_values=user.to_dict(),
            status='success'
        )

        db.session.delete(user)
        db.session.commit()

        return {'message': 'User deleted successfully'}

    @staticmethod
    def get_sessions(current_user):
        sessions = Session.query.filter_by(
            user_id=current_user.id,
            is_revoked=False
        ).order_by(Session.created_at.desc()).all()

        return [s.to_dict() for s in sessions]

    @staticmethod
    def revoke_session(session_id, current_user):
        session = Session.query.get(session_id)

        if not session:
            raise NotFoundError('Session not found')

        if session.user_id != current_user.id and not current_user.has_permission('users.write'):
            raise AuthorizationError('Insufficient permissions')

        session.revoke('Revoked by user')
        db.session.commit()

        return {'message': 'Session revoked'}

    @staticmethod
    def get_audit_logs(query_params, current_user):
        if not current_user.has_permission('audit.read'):
            raise AuthorizationError('Insufficient permissions')

        query = AuditLog.query

        if query_params.get('user_id'):
            query = query.filter(AuditLog.user_id == query_params['user_id'])
        if query_params.get('action'):
            query = query.filter(AuditLog.action.ilike(f"%{query_params['action']}%"))
        if query_params.get('resource_type'):
            query = query.filter(AuditLog.resource_type == query_params['resource_type'])
        if query_params.get('status'):
            query = query.filter(AuditLog.status == query_params['status'])
        if query_params.get('date_from'):
            query = query.filter(AuditLog.created_at >= query_params['date_from'])
        if query_params.get('date_to'):
            query = query.filter(AuditLog.created_at <= query_params['date_to'])

        query = query.order_by(AuditLog.created_at.desc())

        page = query_params.get('page', 1)
        per_page = min(query_params.get('per_page', 50), 100)

        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        return {
            'items': [log.to_dict() for log in pagination.items],
            'total': pagination.total,
            'page': pagination.page,
            'per_page': pagination.per_page,
            'pages': pagination.pages
        }

    @staticmethod
    def _log_audit(user_id, action, resource_type, resource_id=None, description=None,
                   old_values=None, new_values=None, status='success', error_message=None,
                   duration_ms=None, metadata=None):
        try:
            audit = AuditLog(
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                description=description,
                old_values=old_values,
                new_values=new_values,
                ip_address=request.remote_addr if request else None,
                user_agent=request.user_agent.string if request else None,
                status=status,
                error_message=error_message,
                duration_ms=duration_ms,
                metadata=metadata
            )
            db.session.add(audit)
        except Exception:
            pass