from flask import Blueprint


def register_blueprints(app):
    from app.api.auth import auth_bp
    from app.api.ships import ships_bp
    from app.api.containers import containers_bp
    from app.api.dashboard import dashboard_bp
    from app.api.trucks import trucks_bp
    from app.api.security import security_bp
    from app.api.maintenance import maintenance_bp
    from app.api.environment import environment_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(ships_bp)
    app.register_blueprint(containers_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(trucks_bp)
    app.register_blueprint(security_bp)
    app.register_blueprint(maintenance_bp)
    app.register_blueprint(environment_bp)