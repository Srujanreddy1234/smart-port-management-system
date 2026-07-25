import os
from datetime import timedelta
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_mail import Mail
from flask_caching import Cache


db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
bcrypt = Bcrypt()
mail = Mail()
cache = Cache()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["2000 per day", "500 per hour"],
    storage_uri="memory://",
)


def create_app(config_name=None):
    app = Flask(__name__)
    
    config_name = config_name or os.getenv('FLASK_ENV', 'development')
    app.config.from_object(f'config.{config_name.capitalize()}Config')
    
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    bcrypt.init_app(app)
    mail.init_app(app)
    cache.init_app(app)
    limiter.init_app(app)
    CORS(app, resources={r"/api/*": {"origins": app.config.get('CORS_ORIGINS', '*')}}, supports_credentials=True)
    
    from app.api import register_blueprints
    register_blueprints(app)
    
    from app.utils.error_handlers import register_error_handlers
    register_error_handlers(app)
    
    from app.utils.jwt_handlers import register_jwt_handlers
    register_jwt_handlers(jwt)
    
    with app.app_context():
        db.create_all()
    
    @app.shell_context_processor
    def make_shell_context():
        return {'db': db, 'app': app}
    
    return app