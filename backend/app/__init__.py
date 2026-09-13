import os
from flask import Flask, jsonify, send_from_directory
from flask_migrate import Migrate
from config import config
from app.extensions import db, migrate, jwt, bcrypt, mail, cache, limiter, oauth


def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    app = Flask(__name__)
    app.config.from_object(config[config_name])

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    bcrypt.init_app(app)
    mail.init_app(app)
    cache.init_app(app)
    limiter.init_app(app)
    oauth.init_app(app)
    oauth.register(
        name='google',
        client_id=app.config.get('GOOGLE_CLIENT_ID'),
        client_secret=app.config.get('GOOGLE_CLIENT_SECRET'),
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={'scope': 'openid email profile'},
    )

    # CORS
    from flask_cors import CORS
    CORS(app, resources={r"/api/*": {"origins": app.config.get('CORS_ORIGINS', '*')}}, supports_credentials=True)

    from app.api import register_blueprints
    register_blueprints(app)

    from app.utils.error_handlers import register_error_handlers
    register_error_handlers(app)

    from app.utils.jwt_handlers import register_jwt_handlers
    register_jwt_handlers(jwt)

    @app.after_request
    def add_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['Referrer-Policy'] = 'same-origin'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        if not app.config.get('DEBUG'):
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        return response

    from app.utils.helpers import register_cli_commands
    register_cli_commands(app)

    @app.route('/health')
    def health_check():
        # This must work WITHOUT database connection
        return jsonify({'status': 'healthy', 'service': 'Smart Port Management System'}), 200

    @app.route('/api')
    def api_index():
        return jsonify({
            'name': 'Smart Port Management System API',
            'version': '1.0.0',
            'documentation': '/api/docs',
            'status': 'operational'
        }), 200

    # Schema is managed by Alembic (flask db upgrade), run as a release step
    # before the app starts -- see Procfile/railway.toml. Not initialized here
    # so a genuinely missing/incompatible schema fails loudly instead of a
    # silent create_all() masking a migration that was never applied.

    FRONTEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')

    @app.route('/', defaults={'path': 'dashboard.html'})
    @app.route('/<path:path>')
    def serve_frontend(path):
        if path.startswith('api/') or path.startswith('health'):
            return jsonify({'error': 'Not Found'}), 404
        try:
            return send_from_directory(FRONTEND_DIR, path)
        except Exception:
            return jsonify({'error': 'Not Found'}), 404

    return app