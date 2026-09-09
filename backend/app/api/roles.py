from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import Schema, fields, validate, ValidationError
from app.extensions import db
from app.models import Role, Permission, RolePermission, User, UserRole
from app.utils.exceptions import ValidationError as AppValidationError, NotFoundError, AuthorizationError
from app.utils.helpers import success_response
from sqlalchemy import func, desc
from datetime import datetime


roles_bp = Blueprint('roles', __name__, url_prefix='/api/v1/roles')


class RoleCreateSchema(Schema):
    name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    display_name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    description = fields.Str()
    permission_ids = fields.List(fields.Int(), load_default=[])


@roles_bp.route('', methods=['GET'])
@jwt_required()
def list_roles():
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    if not current_user or not current_user.has_permission('roles.read'):
        raise AuthorizationError('Insufficient permissions')

    roles = Role.query.order_by(Role.name).all()
    return success_response({'items': [r.to_dict() for r in roles], 'total': len(roles)})


@roles_bp.route('/<int:role_id>', methods=['GET'])
@jwt_required()
def get_role(role_id):
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    if not current_user or not current_user.has_permission('roles.read'):
        raise AuthorizationError('Insufficient permissions')

    role = Role.query.get(role_id)
    if not role:
        raise NotFoundError('Role not found')
    return success_response(role.to_dict())


@roles_bp.route('', methods=['POST'])
@jwt_required()
def create_role():
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    if not current_user or not current_user.has_permission('roles.write'):
        raise AuthorizationError('Insufficient permissions')

    try:
        data = RoleCreateSchema().load(request.get_json() or {})
    except ValidationError as err:
        return jsonify({'success': False, 'errors': err.messages}), 400

    if Role.query.filter_by(name=data['name']).first():
        raise AppValidationError('Role name already exists')

    role = Role(
        name=data['name'],
        display_name=data['display_name'],
        description=data.get('description'),
        is_system=False,
    )

    if data.get('permission_ids'):
        permissions = Permission.query.filter(Permission.id.in_(data['permission_ids'])).all()
        role.permissions = permissions

    db.session.add(role)
    db.session.commit()

    return success_response(role.to_dict(), 'Role created successfully', 201)


@roles_bp.route('/<int:role_id>', methods=['PUT'])
@jwt_required()
def update_role(role_id):
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    if not current_user or not current_user.has_permission('roles.write'):
        raise AuthorizationError('Insufficient permissions')

    role = Role.query.get(role_id)
    if not role:
        raise NotFoundError('Role not found')

    if role.is_system:
        raise AppValidationError('Cannot modify system roles')

    try:
        data = RoleCreateSchema().load(request.get_json() or {}, partial=True)
    except ValidationError as err:
        return jsonify({'success': False, 'errors': err.messages}), 400

    if 'name' in data and data['name'] != role.name:
        if Role.query.filter_by(name=data['name']).first():
            raise AppValidationError('Role name already exists')
        role.name = data['name']

    if 'display_name' in data:
        role.display_name = data['display_name']
    if 'description' in data:
        role.description = data['description']

    if 'permission_ids' in data:
        permissions = Permission.query.filter(Permission.id.in_(data['permission_ids'])).all()
        role.permissions = permissions

    role.updated_at = datetime.utcnow()
    db.session.commit()

    return success_response(role.to_dict(), 'Role updated successfully')


@roles_bp.route('/<int:role_id>', methods=['DELETE'])
@jwt_required()
def delete_role(role_id):
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    if not current_user or not current_user.has_permission('roles.delete'):
        raise AuthorizationError('Insufficient permissions')

    role = Role.query.get(role_id)
    if not role:
        raise NotFoundError('Role not found')

    if role.is_system:
        raise AppValidationError('Cannot delete system roles')

    user_count = User.query.filter(User.role == role.name).count()
    if user_count > 0:
        raise AppValidationError(f'Cannot delete role assigned to {user_count} users')

    db.session.delete(role)
    db.session.commit()

    return success_response(None, 'Role deleted')


@roles_bp.route('/permissions', methods=['GET'])
@jwt_required()
def list_permissions():
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    if not current_user or not current_user.has_permission('roles.read'):
        raise AuthorizationError('Insufficient permissions')

    permissions = Permission.query.order_by(Permission.module, Permission.action).all()

    grouped = {}
    for p in permissions:
        if p.module not in grouped:
            grouped[p.module] = []
        grouped[p.module].append(p.to_dict())

    return success_response({'items': [p.to_dict() for p in permissions], 'grouped': grouped, 'total': len(permissions)})