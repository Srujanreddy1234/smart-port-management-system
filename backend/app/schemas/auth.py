from marshmallow import Schema, fields, validate, validates, ValidationError, pre_load
from app.extensions import bcrypt


class UserSchema(Schema):
    id = fields.Int(dump_only=True)
    email = fields.Email(required=True, validate=validate.Length(max=255))
    first_name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    last_name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    role = fields.Str(validate=validate.OneOf([
        'admin', 'operations_officer', 'security_officer', 'environmental_officer', 'viewer'
    ]))
    status = fields.Str(validate=validate.OneOf(['active', 'inactive', 'suspended', 'pending']))
    employee_id = fields.Str(validate=validate.Length(max=50))
    department = fields.Str(validate=validate.Length(max=100))
    designation = fields.Str(validate=validate.Length(max=100))
    phone = fields.Str(validate=validate.Length(max=20))
    mobile = fields.Str(validate=validate.Length(max=20))
    avatar_url = fields.URL()
    two_factor_enabled = fields.Bool()
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    last_login_at = fields.DateTime(dump_only=True)

    full_name = fields.Method('get_full_name')
    initials = fields.Method('get_initials')

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"

    def get_initials(self, obj):
        return f"{obj.first_name[0]}{obj.last_name[0]}".upper()


class UserCreateSchema(UserSchema):
    password = fields.Str(required=True, validate=validate.Length(min=8, max=128), load_only=True)
    confirm_password = fields.Str(required=True, load_only=True)

    @validates('confirm_password')
    def validate_confirm_password(self, value):
        if 'password' in self.context and value != self.context['password']:
            raise ValidationError('Passwords do not match')

    @validates('email')
    def validate_email_unique(self, value):
        from app.models.user import User
        if User.query.filter_by(email=value.lower()).first():
            raise ValidationError('Email already registered')


class UserUpdateSchema(Schema):
    first_name = fields.Str(validate=validate.Length(min=1, max=100))
    last_name = fields.Str(validate=validate.Length(min=1, max=100))
    role = fields.Str(validate=validate.OneOf([
        'admin', 'operations_officer', 'security_officer', 'environmental_officer', 'viewer'
    ]))
    status = fields.Str(validate=validate.OneOf(['active', 'inactive', 'suspended', 'pending']))
    employee_id = fields.Str(validate=validate.Length(max=50))
    department = fields.Str(validate=validate.Length(max=100))
    designation = fields.Str(validate=validate.Length(max=100))
    phone = fields.Str(validate=validate.Length(max=20))
    mobile = fields.Str(validate=validate.Length(max=20))
    avatar_url = fields.URL()
    two_factor_enabled = fields.Bool()


class UserPasswordUpdateSchema(Schema):
    current_password = fields.Str(required=True, load_only=True)
    new_password = fields.Str(required=True, validate=validate.Length(min=8, max=128), load_only=True)
    confirm_password = fields.Str(required=True, load_only=True)

    @validates('confirm_password')
    def validate_confirm_password(self, value):
        if 'new_password' in self.context and value != self.context['new_password']:
            raise ValidationError('Passwords do not match')


class LoginSchema(Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=True, load_only=True)
    remember_me = fields.Bool()


class TokenSchema(Schema):
    access_token = fields.Str()
    refresh_token = fields.Str()
    token_type = fields.Str(default='Bearer')
    expires_in = fields.Int()
    user = fields.Nested(UserSchema)


class SessionSchema(Schema):
    id = fields.Int(dump_only=True)
    token = fields.Str(dump_only=True)
    user_agent = fields.Str()
    ip_address = fields.Str()
    device_info = fields.Dict()
    expires_at = fields.DateTime(dump_only=True)
    is_revoked = fields.Bool(dump_only=True)
    created_at = fields.DateTime(dump_only=True)


class AuditLogSchema(Schema):
    id = fields.Int(dump_only=True)
    user_id = fields.Int()
    action = fields.Str()
    resource_type = fields.Str()
    resource_id = fields.Str()
    description = fields.Str()
    old_values = fields.Dict()
    new_values = fields.Dict()
    ip_address = fields.Str()
    user_agent = fields.Str()
    status = fields.Str()
    error_message = fields.Str()
    duration_ms = fields.Int()
    metadata = fields.Dict()
    created_at = fields.DateTime(dump_only=True)
    user = fields.Nested(UserSchema, only=['id', 'email', 'first_name', 'last_name'])


class PaginationSchema(Schema):
    page = fields.Int(load_default=1, validate=validate.Range(min=1))
    per_page = fields.Int(load_default=20, validate=validate.Range(min=1, max=100))
    sort_by = fields.Str()
    sort_order = fields.Str(validate=validate.OneOf(['asc', 'desc']))
    search = fields.Str()


class UserQuerySchema(PaginationSchema):
    role = fields.Str()
    status = fields.Str()
    department = fields.Str()
    email_verified = fields.Bool()


user_schema = UserSchema()
user_create_schema = UserCreateSchema()
user_update_schema = UserUpdateSchema()
user_password_schema = UserPasswordUpdateSchema()
login_schema = LoginSchema()
token_schema = TokenSchema()
session_schema = SessionSchema()
audit_log_schema = AuditLogSchema()
pagination_schema = PaginationSchema()
user_query_schema = UserQuerySchema()