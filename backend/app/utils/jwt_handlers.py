from flask import jsonify
from flask_jwt_extended import JWTManager
from app.extensions import db
from app.models import Session, User


def register_jwt_handlers(jwt: JWTManager):
    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        jti = jwt_payload['jti']
        token_type = jwt_payload.get('type', 'access')
        
        session = Session.query.filter_by(token=jti).first()
        if session is None:
            return False
        return session.is_revoked

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({
            'success': False,
            'message': 'Token has expired',
            'error': 'token_expired',
        }), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({
            'success': False,
            'message': 'Invalid token',
            'error': 'invalid_token',
        }), 401

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({
            'success': False,
            'message': 'Authorization token is required',
            'error': 'authorization_required',
        }), 401

    @jwt.needs_fresh_token_loader
    def token_not_fresh_callback(jwt_header, jwt_payload):
        return jsonify({
            'success': False,
            'message': 'Fresh token required',
            'error': 'fresh_token_required',
        }), 401

    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        return jsonify({
            'success': False,
            'message': 'Token has been revoked',
            'error': 'token_revoked',
        }), 401

    @jwt.user_identity_loader
    def user_identity_lookup(user_id):
        return str(user_id)

    @jwt.user_lookup_loader
    def user_lookup_callback(jwt_header, jwt_data):
        identity = jwt_data['sub']
        return User.query.filter_by(id=identity).first()

    @jwt.additional_claims_loader
    def add_claims_to_access_token(identity):
        user = User.query.get(identity)
        if user:
            return {
                'role': user.role.value,
                'email': user.email,
                'full_name': user.get_full_name(),
            }
        return {}