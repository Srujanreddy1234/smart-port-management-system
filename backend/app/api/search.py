from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
from app.models import Ship, Container, Truck, User
from app.utils.helpers import success_response


search_bp = Blueprint('search', __name__, url_prefix='/api/v1/search')


@search_bp.route('', methods=['GET'])
@jwt_required()
def global_search():
    user = User.query.get(get_jwt_identity())
    q = request.args.get('q', '').strip()
    result = {'ships': [], 'containers': [], 'trucks': [], 'users': []}
    if not q or len(q) < 2 or not user:
        return success_response(result)

    pattern = f'%{q}%'

    if user.has_permission('ships.read'):
        ships = Ship.query.filter(
            db.or_(
                Ship.name.ilike(pattern),
                Ship.ship_id.ilike(pattern),
                Ship.imo_number.ilike(pattern),
                Ship.agent.ilike(pattern),
            )
        ).limit(10).all()
        result['ships'] = [{'id': s.id, 'name': s.name, 'ship_id': s.ship_id, 'status': s.status.value} for s in ships]

    if user.has_permission('containers.read'):
        containers = Container.query.filter(
            db.or_(
                Container.container_id.ilike(pattern),
                Container.owner.ilike(pattern),
                Container.seal_number.ilike(pattern),
            )
        ).limit(10).all()
        result['containers'] = [{'id': c.id, 'container_id': c.container_id, 'status': c.status.value, 'owner': c.owner} for c in containers]

    if user.has_permission('trucks.read'):
        trucks = Truck.query.filter(
            db.or_(
                Truck.truck_number.ilike(pattern),
                Truck.driver_name.ilike(pattern),
                Truck.license_plate.ilike(pattern),
            )
        ).limit(10).all()
        result['trucks'] = [{'id': t.id, 'truck_number': t.truck_number, 'driver_name': t.driver_name, 'status': t.status.value} for t in trucks]

    if user.has_permission('users.read'):
        users = User.query.filter(
            db.or_(
                User.first_name.ilike(pattern),
                User.last_name.ilike(pattern),
                User.email.ilike(pattern),
                User.employee_id.ilike(pattern),
            )
        ).limit(10).all()
        result['users'] = [{'id': u.id, 'full_name': u.get_full_name(), 'email': u.email, 'role': u.role.value} for u in users]

    return success_response(result)