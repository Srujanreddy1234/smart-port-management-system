from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from marshmallow import Schema, fields, validate, ValidationError
from app.extensions import db
from app.models import User, UserRole, UserStatus
from app.utils.exceptions import ValidationError as AppValidationError, NotFoundError, AuthorizationError
from app.utils.helpers import success_response, paginate_query
from sqlalchemy import func, or_, desc
from datetime import datetime


users_bp = Blueprint('users', __name__, url_prefix='/api/v1/users')


class UserCreateSchema(Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=True, validate=validate.Length(min=8))
    first_name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    last_name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    role = fields.Str(required=True, validate=validate.OneOf([r.value for r in UserRole]))
    employee_id = fields.Str(validate=validate.Length(max=50))
    department = fields.Str(validate=validate.Length(max=100))
    designation = fields.Str(validate=validate.Length(max=100))
    phone = fields.Str(validate=validate.Length(max=20))
    mobile = fields.Str(validate=validate.Length(max=20))


class UserUpdateSchema(Schema):
    first_name = fields.Str(validate=validate.Length(min=1, max=100))
    last_name = fields.Str(validate=validate.Length(min=1, max=100))
    role = fields.Str(validate=validate.OneOf([r.value for r in UserRole]))
    status = fields.Str(validate=validate.OneOf([s.value for s in UserStatus]))
    employee_id = fields.Str(validate=validate.Length(max=50))
    department = fields.Str(validate=validate.Length(max=100))
    designation = fields.Str(validate=validate.Length(max=100))
    phone = fields.Str(validate=validate.Length(max=20))
    mobile = fields.Str(validate=validate.Length(max=20))


@users_bp.route('', methods=['GET'])
@jwt_required()
def list_users():
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    if not current_user or not current_user.has_permission('users.read'):
        raise AuthorizationError('Insufficient permissions')

    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)
    search = request.args.get('search', '').strip()
    status = request.args.get('status')
    role = request.args.get('role')
    department = request.args.get('department')
    sort_by = request.args.get('sort_by', 'created_at')
    sort_order = request.args.get('sort_order', 'desc')

    query = User.query

    if search:
        query = query.filter(or_(
            User.first_name.ilike(f'%{search}%'),
            User.last_name.ilike(f'%{search}%'),
            User.email.ilike(f'%{search}%'),
            User.employee_id.ilike(f'%{search}%'),
        ))

    if status:
        try:
            query = query.filter(User.status == UserStatus(status))
        except ValueError:
            raise AppValidationError(f'Invalid status: {status}')

    if role:
        try:
            query = query.filter(User.role == UserRole(role))
        except ValueError:
            raise AppValidationError(f'Invalid role: {role}')

    if department:
        query = query.filter(User.department == department)

    sort_column = getattr(User, sort_by, User.created_at)
    if sort_order == 'desc':
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(sort_column)

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return success_response({
        'items': [u.to_list_dict() for u in pagination.items],
        'total': pagination.total,
        'page': pagination.page,
        'per_page': pagination.per_page,
        'pages': pagination.pages,
        'has_next': pagination.has_next,
        'has_prev': pagination.has_prev
    })


@users_bp.route('/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user(user_id):
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    if not current_user or not current_user.has_permission('users.read'):
        raise AuthorizationError('Insufficient permissions')

    user = User.query.get(user_id)
    if not user:
        raise NotFoundError('User not found')
    return success_response(user.to_dict(include_sensitive=True))


@users_bp.route('', methods=['POST'])
@jwt_required()
def create_user():
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    if not current_user or not current_user.has_permission('users.write'):
        raise AuthorizationError('Insufficient permissions')

    try:
        data = UserCreateSchema().load(request.get_json() or {})
    except ValidationError as err:
        return jsonify({'success': False, 'errors': err.messages}), 400

    email = data['email'].lower()
    if User.query.filter_by(email=email).first():
        raise AppValidationError('An account with this email already exists')

    if data.get('employee_id') and User.query.filter_by(employee_id=data['employee_id']).first():
        raise AppValidationError('Employee ID already exists')

    target_role = UserRole(data['role'])
    if current_user.role != UserRole.SUPER_ADMIN and target_role in [UserRole.SUPER_ADMIN, UserRole.ADMIN]:
        raise AuthorizationError('Insufficient permissions to create admin users')

    user = User(
        email=email,
        first_name=data['first_name'],
        last_name=data['last_name'],
        role=target_role,
        status=UserStatus.ACTIVE,
        employee_id=data.get('employee_id'),
        department=data.get('department'),
        designation=data.get('designation'),
        phone=data.get('phone'),
        mobile=data.get('mobile'),
    )
    user.set_password(data['password'])
    db.session.add(user)
    db.session.commit()

    return success_response(user.to_dict(), 'User created successfully', 201)


@users_bp.route('/<int:user_id>', methods=['PUT'])
@jwt_required()
def update_user(user_id):
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    if not current_user or not current_user.has_permission('users.write'):
        raise AuthorizationError('Insufficient permissions')

    user = User.query.get(user_id)
    if not user:
        raise NotFoundError('User not found')

    try:
        data = UserUpdateSchema().load(request.get_json() or {}, partial=True)
    except ValidationError as err:
        return jsonify({'success': False, 'errors': err.messages}), 400

    if 'role' in data:
        target_role = UserRole(data['role'])
        if current_user.role != UserRole.SUPER_ADMIN and target_role in [UserRole.SUPER_ADMIN, UserRole.ADMIN]:
            raise AuthorizationError('Insufficient permissions to assign admin roles')
        user.role = target_role

    if 'status' in data:
        user.status = UserStatus(data['status'])

    for key in ['first_name', 'last_name', 'employee_id', 'department', 'designation', 'phone', 'mobile']:
        if key in data:
            setattr(user, key, data[key])

    user.updated_at = datetime.utcnow()
    db.session.commit()

    return success_response(user.to_dict(), 'User updated successfully')


@users_bp.route('/<int:user_id>', methods=['DELETE'])
@jwt_required()
def delete_user(user_id):
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    if not current_user or not current_user.has_permission('users.delete'):
        raise AuthorizationError('Insufficient permissions')

    user = User.query.get(user_id)
    if not user:
        raise NotFoundError('User not found')

    if user.id == current_user_id:
        raise AppValidationError('Cannot delete your own account')

    if user.role in [UserRole.SUPER_ADMIN, UserRole.ADMIN] and current_user.role != UserRole.SUPER_ADMIN:
        raise AuthorizationError('Cannot delete admin users')

    user.status = UserStatus.INACTIVE
    user.updated_at = datetime.utcnow()
    db.session.commit()

    return success_response(None, 'User deactivated')


@users_bp.route('/<int:user_id>/reset-password', methods=['POST'])
@jwt_required()
def reset_user_password(user_id):
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    if not current_user or not current_user.has_permission('users.write'):
        raise AuthorizationError('Insufficient permissions')

    user = User.query.get(user_id)
    if not user:
        raise NotFoundError('User not found')

    import secrets
    new_password = secrets.token_urlsafe(12)
    user.set_password(new_password)
    user.must_change_password = True
    db.session.commit()

    return success_response({'new_password': new_password}, 'Password reset successfully')


@users_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_user_stats():
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    if not current_user or not current_user.has_permission('users.read'):
        raise AuthorizationError('Insufficient permissions')

    total = User.query.count()
    by_status = db.session.query(User.status, func.count(User.id)).group_by(User.status).all()
    by_role = db.session.query(User.role, func.count(User.id)).group_by(User.role).all()
    by_department = db.session.query(User.department, func.count(User.id)).filter(User.department.isnot(None)).group_by(User.department).all()

    return success_response({
        'total': total,
        'by_status': {s.value: c for s, c in by_status},
        'by_role': {r.value: c for r, c in by_role},
        'by_department': {d: c for d, c in by_department if d}
    })