from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
from app.models import Ship, Container, Truck, User
from app.utils.helpers import success_response


search_bp = Blueprint('search', __name__, url_prefix='/api/v1/search')


@search_bp.route('', methods=['GET'])
@jwt_required()
def global_search():
    q = request.args.get('q', '').strip()
    if not q or len(q) < 2:
        return success_response({'ships': [], 'containers': [], 'trucks': [], 'users': []})

    pattern = f'%{q}%'

    ships = Ship.query.filter(
        db.or_(
            Ship.name.ilike(pattern),
            Ship.ship_id.ilike(pattern),
            Ship.imo_number.ilike(pattern),
            Ship.agent.ilike(pattern),
        )
    ).limit(10).all()

    containers = Container.query.filter(
        db.or_(
            Container.container_id.ilike(pattern),
            Container.owner.ilike(pattern),
            Container.seal_number.ilike(pattern),
        )
    ).limit(10).all()

    trucks = Truck.query.filter(
        db.or_(
            Truck.truck_number.ilike(pattern),
            Truck.driver_name.ilike(pattern),
            Truck.license_plate.ilike(pattern),
        )
    ).limit(10).all()

    users = User.query.filter(
        db.or_(
            User.first_name.ilike(pattern),
            User.last_name.ilike(pattern),
            User.email.ilike(pattern),
            User.employee_id.ilike(pattern),
        )
    ).limit(10).all()

    return success_response({
        'ships': [{'id': s.id, 'name': s.name, 'ship_id': s.ship_id, 'status': s.status.value} for s in ships],
        'containers': [{'id': c.id, 'container_id': c.container_id, 'status': c.status.value, 'owner': c.owner} for c in containers],
        'trucks': [{'id': t.id, 'truck_number': t.truck_number, 'driver_name': t.driver_name, 'status': t.status.value} for t in trucks],
        'users': [{'id': u.id, 'full_name': u.get_full_name(), 'email': u.email, 'role': u.role.value} for u in users],
    })