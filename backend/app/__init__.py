from flask import Flask, jsonify
from flask_migrate import Migrate
from config import config
from app.extensions import init_extensions
import os


def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    app = Flask(__name__)
    app.config.from_object(config[config_name])

    init_extensions(app)

    from app.api import register_blueprints
    register_blueprints(app)

    from app.utils.exceptions import register_error_handlers
    register_error_handlers(app)

    from app.utils.helpers import register_cli_commands
    register_cli_commands(app)

    @app.route('/health')
    def health_check():
        return jsonify({'status': 'healthy', 'service': 'Smart Port Management System'}), 200

    @app.route('/api')
    def api_index():
        return jsonify({
            'name': 'Smart Port Management System API',
            'version': '1.0.0',
            'documentation': '/api/docs',
            'status': 'operational'
        }), 200

    with app.app_context():
        from app.models import *
        db.create_all()

    return app