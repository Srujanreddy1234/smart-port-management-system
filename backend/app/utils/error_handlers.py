from flask import jsonify
from werkzeug.exceptions import HTTPException
from marshmallow import ValidationError as MarshmallowValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from app.utils.exceptions import (
    AppException, ValidationError, AuthenticationError,
    AuthorizationError, NotFoundError, ConflictError, RateLimitError
)


def register_error_handlers(app):
    @app.errorhandler(AppException)
    def handle_app_exception(e):
        response = {
            'success': False,
            'message': e.message,
        }
        if e.errors:
            response['errors'] = e.errors
        if e.details:
            response['details'] = e.details
        return jsonify(response), e.status_code

    @app.errorhandler(MarshmallowValidationError)
    def handle_marshmallow_validation(e):
        return jsonify({
            'success': False,
            'message': 'Validation failed',
            'errors': e.messages,
        }), 400

    @app.errorhandler(IntegrityError)
    def handle_integrity_error(e):
        return jsonify({
            'success': False,
            'message': 'Database integrity error',
            'errors': {'database': 'A record with this value already exists'},
        }), 409

    @app.errorhandler(SQLAlchemyError)
    def handle_sqlalchemy_error(e):
        app.logger.error(f'Database error: {e}')
        return jsonify({
            'success': False,
            'message': 'Database error occurred',
        }), 500

    @app.errorhandler(HTTPException)
    def handle_http_exception(e):
        return jsonify({
            'success': False,
            'message': e.description,
        }), e.code

    @app.errorhandler(429)
    def handle_rate_limit(e):
        return jsonify({
            'success': False,
            'message': 'Rate limit exceeded. Please try again later.',
        }), 429

    @app.errorhandler(500)
    def handle_internal_error(e):
        app.logger.error(f'Internal server error: {e}')
        return jsonify({
            'success': False,
            'message': 'Internal server error',
        }), 500

    @app.errorhandler(Exception)
    def handle_generic_exception(e):
        app.logger.error(f'Unhandled exception: {e}', exc_info=True)
        if app.debug:
            return jsonify({
                'success': False,
                'message': str(e),
                'type': type(e).__name__,
            }), 500
        return jsonify({
            'success': False,
            'message': 'An unexpected error occurred',
        }), 500