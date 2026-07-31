from flask import Blueprint, request, jsonify, current_app, redirect, url_for
from flask_jwt_extended import (
    create_access_token, create_refresh_token, jwt_required,
    get_jwt_identity, get_jwt, verify_jwt_in_request
)
from marshmallow import Schema, fields, validate, ValidationError
from werkzeug.security import check_password_hash
from app.extensions import db, limiter, oauth
from app.models import User, Session, AuditLog, UserRole, UserStatus
from app.services.auth_service import AuthService
from app.utils.exceptions import ValidationError as AppValidationError, AuthenticationError, AuthorizationError
from app.utils.helpers import success_response, error_response, paginate_query
import uuid
from datetime import datetime, timedelta


auth_bp = Blueprint('auth', __name__, url_prefix='/api/v1/auth')


class LoginSchema(Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=True, validate=validate.Length(min=1))
    remember_me = fields.Bool(load_default=False)


class RegisterSchema(Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=True, validate=validate.Length(min=8))
    first_name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    last_name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    role = fields.Str(validate=validate.OneOf(['admin', 'operations_officer', 'security_officer', 'environmental_officer', 'viewer']))
    employee_id = fields.Str(validate=validate.Length(max=50))
    department = fields.Str(validate=validate.Length(max=100))
    designation = fields.Str(validate=validate.Length(max=100))
    phone = fields.Str(validate=validate.Length(max=20))
    mobile = fields.Str(validate=validate.Length(max=20))


class ChangePasswordSchema(Schema):
    current_password = fields.Str(required=True)
    new_password = fields.Str(required=True, validate=validate.Length(min=8))
    confirm_password = fields.Str(required=True)


class ForgotPasswordSchema(Schema):
    email = fields.Email(required=True)


class ResetPasswordSchema(Schema):
    token = fields.Str(required=True)
    password = fields.Str(required=True, validate=validate.Length(min=8))
    confirm_password = fields.Str(required=True)


def get_client_ip():
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    return request.remote_addr


def get_user_agent():
    return request.headers.get('User-Agent', '')


@auth_bp.route('/login', methods=['POST'])
@limiter.limit("10 per minute")
def login():
    schema = LoginSchema()
    try:
        data = schema.load(request.get_json() or {})
    except ValidationError as err:
        return error_response('Validation failed', errors=err.messages, status_code=400)

    user = User.query.filter_by(email=data['email'].lower()).first()

    if not user or not user.check_password(data['password']):
        if user:
            user.record_failed_login()
            db.session.commit()
        AuthService._log_audit(
            user_id=user.id if user else None,
            action='login',
            resource_type='auth',
            status='failed',
            error_message='Invalid credentials'
        )
        raise AuthenticationError('Invalid email or password')

    if not user.is_active():
        raise AuthenticationError('Account is not active')

    if user.is_locked():
        raise AuthenticationError('Account temporarily locked. Try again later.')

    user.record_successful_login(get_client_ip())
    
    access_token = create_access_token(
        identity=str(user.id),
        additional_claims={
            'role': user.role.value,
            'email': user.email,
            'full_name': user.get_full_name()
        }
    )
    
    refresh_token = create_refresh_token(identity=str(user.id))

    session = Session(
        user_id=user.id,
        token=access_token,
        refresh_token=refresh_token,
        user_agent=get_user_agent(),
        ip_address=get_client_ip(),
        device_info={
            'platform': request.user_agent.platform,
            'browser': request.user_agent.browser,
            'version': request.user_agent.version
        },
        expires_at=datetime.utcnow() + timedelta(hours=2),
        refresh_expires_at=datetime.utcnow() + timedelta(days=30 if data.get('remember_me') else 7)
    )
    db.session.add(session)
    db.session.commit()

    AuthService._log_audit(
        user_id=user.id,
        action='login',
        resource_type='auth',
        status='success'
    )

    return success_response({
        'access_token': access_token,
        'refresh_token': refresh_token,
        'token_type': 'Bearer',
        'expires_in': 7200,
        'user': user.to_dict()
    }, 'Login successful')


@auth_bp.route('/register', methods=['POST'])
@limiter.limit("10 per hour")
def register():
    schema = RegisterSchema()
    try:
        data = schema.load(request.get_json() or {})
    except ValidationError as err:
        return error_response('Validation failed', errors=err.messages, status_code=400)

    email = data['email'].lower()
    if User.query.filter_by(email=email).first():
        raise AppValidationError('An account with this email already exists')

    user = User(
        email=email,
        first_name=data['first_name'],
        last_name=data['last_name'],
        role=UserRole.VIEWER,
        status=UserStatus.ACTIVE,
        department=data.get('department'),
        designation=data.get('designation'),
        phone=data.get('phone'),
        mobile=data.get('mobile')
    )
    user.set_password(data['password'])
    db.session.add(user)
    db.session.commit()

    access_token = create_access_token(
        identity=str(user.id),
        additional_claims={'role': user.role.value, 'email': user.email, 'full_name': user.get_full_name()}
    )
    refresh_token = create_refresh_token(identity=str(user.id))

    session = Session(
        user_id=user.id,
        token=access_token,
        refresh_token=refresh_token,
        user_agent=get_user_agent(),
        ip_address=get_client_ip(),
        device_info={'platform': request.user_agent.platform, 'browser': request.user_agent.browser, 'version': request.user_agent.version},
        expires_at=datetime.utcnow() + timedelta(hours=2),
        refresh_expires_at=datetime.utcnow() + timedelta(days=7)
    )
    db.session.add(session)
    db.session.commit()

    AuthService._log_audit(user_id=user.id, action='register', resource_type='auth', status='success')

    return success_response({
        'access_token': access_token,
        'refresh_token': refresh_token,
        'token_type': 'Bearer',
        'expires_in': 7200,
        'user': user.to_dict()
    }, 'Account created successfully', 201)


@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    current_user_id = get_jwt_identity()
    jti = get_jwt()['jti']
    
    session = Session.query.filter_by(token=request.headers.get('Authorization', '').replace('Bearer ', '')).first()
    if session:
        session.revoke('User logout')
        db.session.commit()

    AuthService._log_audit(
        user_id=current_user_id,
        action='logout',
        resource_type='auth',
        status='success'
    )

    return success_response(None, 'Logged out successfully')


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user or not user.is_active():
        raise AuthenticationError('User not found or inactive')

    access_token = create_access_token(
        identity=str(user.id),
        additional_claims={
            'role': user.role.value,
            'email': user.email,
            'full_name': user.get_full_name()
        }
    )

    session = Session.query.filter_by(
        user_id=user.id,
        refresh_token=request.headers.get('Authorization', '').replace('Bearer ', '')
    ).first()
    
    if session and session.is_refresh_valid():
        session.token = access_token
        session.expires_at = datetime.utcnow() + timedelta(hours=2)
        db.session.commit()

    return success_response({
        'access_token': access_token,
        'token_type': 'Bearer',
        'expires_in': 7200
    }, 'Token refreshed')


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        raise AuthenticationError('User not found')

    return success_response(user.to_dict(include_sensitive=True))


@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    schema = ChangePasswordSchema()
    try:
        data = schema.load(request.get_json() or {})
    except ValidationError as err:
        return error_response('Validation failed', errors=err.messages, status_code=400)

    if data['new_password'] != data['confirm_password']:
        raise AppValidationError('New passwords do not match')

    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user or not user.check_password(data['current_password']):
        raise AuthenticationError('Current password is incorrect')

    user.set_password(data['new_password'])
    db.session.commit()

    AuthService._log_audit(
        user_id=user.id,
        action='change_password',
        resource_type='user',
        resource_id=str(user.id),
        status='success'
    )

    return success_response(None, 'Password changed successfully')


@auth_bp.route('/forgot-password', methods=['POST'])
@limiter.limit("3 per hour")
def forgot_password():
    schema = ForgotPasswordSchema()
    try:
        data = schema.load(request.get_json() or {})
    except ValidationError as err:
        return error_response('Validation failed', errors=err.messages, status_code=400)

    user = User.query.filter_by(email=data['email'].lower()).first()
    
    if user:
        reset_token = str(uuid.uuid4())
        user.reset_token = reset_token
        user.reset_token_expires = datetime.utcnow() + timedelta(hours=1)
        db.session.commit()
        
        # TODO: Send email with reset token
        current_app.logger.info(f"Password reset token for {user.email}: {reset_token}")

    return success_response(None, 'If the email exists, a reset link has been sent')


@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    schema = ResetPasswordSchema()
    try:
        data = schema.load(request.get_json() or {})
    except ValidationError as err:
        return error_response('Validation failed', errors=err.messages, status_code=400)

    if data['password'] != data['confirm_password']:
        raise AppValidationError('Passwords do not match')

    user = User.query.filter_by(reset_token=data['token']).first()
    
    if not user or not user.reset_token_expires or user.reset_token_expires < datetime.utcnow():
        raise AuthenticationError('Invalid or expired reset token')

    user.set_password(data['password'])
    user.reset_token = None
    user.reset_token_expires = None
    db.session.commit()

    AuthService._log_audit(
        user_id=user.id,
        action='reset_password',
        resource_type='user',
        resource_id=str(user.id),
        status='success'
    )

    return success_response(None, 'Password reset successful')


@auth_bp.route('/sessions', methods=['GET'])
@jwt_required()
def get_sessions():
    current_user_id = get_jwt_identity()
    sessions = Session.query.filter_by(user_id=current_user_id, is_revoked=False).order_by(Session.created_at.desc()).all()
    
    return success_response({
        'items': [s.to_dict() for s in sessions],
        'total': len(sessions)
    })


@auth_bp.route('/sessions/<int:session_id>', methods=['DELETE'])
@jwt_required()
def revoke_session(session_id):
    current_user_id = get_jwt_identity()
    session = Session.query.filter_by(id=session_id, user_id=current_user_id).first()
    
    if not session:
        return error_response('Session not found', status_code=404)

    session.revoke('Revoked by user')
    db.session.commit()

    return success_response(None, 'Session revoked')


@auth_bp.route('/revoke-all-sessions', methods=['POST'])
@jwt_required()
def revoke_all_sessions():
    current_user_id = get_jwt_identity()
    current_jti = get_jwt()['jti']
    
    Session.query.filter(
        Session.user_id == current_user_id,
        Session.is_revoked == False,
        Session.token != request.headers.get('Authorization', '').replace('Bearer ', '')
    ).update({'is_revoked': True, 'revoked_at': datetime.utcnow(), 'revoked_reason': 'Revoked all other sessions'})

    db.session.commit()

    return success_response(None, 'All other sessions revoked')


@auth_bp.route('/google/login', methods=['GET'])
def google_login():
    redirect_uri = url_for('auth.google_callback', _external=True)
    return oauth.google.authorize_redirect(redirect_uri)


@auth_bp.route('/google/callback', methods=['GET'])
def google_callback():
    frontend_url = current_app.config.get('FRONTEND_URL', 'http://localhost:5501')
    try:
        token = oauth.google.authorize_access_token()
        userinfo = token.get('userinfo') or oauth.google.userinfo()
    except Exception:
        return redirect(f'{frontend_url}/login.html?error=oauth_failed')

    email = (userinfo.get('email') or '').lower()
    if not email:
        return redirect(f'{frontend_url}/login.html?error=oauth_no_email')

    user = User.query.filter_by(email=email).first()
    if not user:
        user = User(
            email=email,
            first_name=userinfo.get('given_name') or userinfo.get('name') or 'Google',
            last_name=userinfo.get('family_name') or 'User',
            role=UserRole.VIEWER,
            status=UserStatus.ACTIVE,
            email_verified=bool(userinfo.get('email_verified')),
            avatar_url=userinfo.get('picture')
        )
        db.session.add(user)
        db.session.commit()

    if not user.is_active():
        return redirect(f'{frontend_url}/login.html?error=account_inactive')

    user.record_successful_login(get_client_ip())

    access_token = create_access_token(
        identity=str(user.id),
        additional_claims={'role': user.role.value, 'email': user.email, 'full_name': user.get_full_name()}
    )
    refresh_token = create_refresh_token(identity=str(user.id))

    session = Session(
        user_id=user.id,
        token=access_token,
        refresh_token=refresh_token,
        user_agent=get_user_agent(),
        ip_address=get_client_ip(),
        device_info={'platform': None, 'browser': None, 'version': None},
        expires_at=datetime.utcnow() + timedelta(hours=2),
        refresh_expires_at=datetime.utcnow() + timedelta(days=7)
    )
    db.session.add(session)
    db.session.commit()

    AuthService._log_audit(user_id=user.id, action='login', resource_type='auth', status='success')

    return redirect(f'{frontend_url}/oauth-callback.html?access_token={access_token}&refresh_token={refresh_token}')