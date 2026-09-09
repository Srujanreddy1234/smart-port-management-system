from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import Schema, fields, validate, ValidationError
from app.extensions import db
from app.models import User, Ship, Berth
from app.models.billing import Invoice, InvoiceStatus, BillingLine, BillingCategory, PaymentMethod
from app.models.event_log import EventType, EventSeverity
from app.api.sse import publish_event
from app.utils.exceptions import NotFoundError, AuthorizationError, ValidationError as AppValidationError
from app.utils.helpers import success_response, paginate_query
from sqlalchemy import func, or_, desc
from datetime import datetime
import uuid


billing_bp = Blueprint('billing', __name__, url_prefix='/api/v1/billing')


class InvoiceSchema(Schema):
    ship_id = fields.Int(required=True)
    berth_id = fields.Int()
    billing_period_start = fields.DateTime(required=True)
    billing_period_end = fields.DateTime(required=True)
    tax_rate = fields.Float(load_default=0)
    discount = fields.Float(load_default=0)
    due_date = fields.DateTime(required=True)
    notes = fields.Str()
    terms = fields.Str()
    line_items = fields.List(fields.Dict(), load_default=[])


class BillingLineSchema(Schema):
    category = fields.Str(required=True, validate=validate.OneOf([c.value for c in BillingCategory]))
    description = fields.Str(required=True, validate=validate.Length(max=500))
    quantity = fields.Float(load_default=1)
    unit = fields.Str()
    unit_price = fields.Float(required=True)
    notes = fields.Str()


class PaymentSchema(Schema):
    amount = fields.Float(required=True)
    payment_method = fields.Str(required=True, validate=validate.OneOf([p.value for p in PaymentMethod]))
    payment_reference = fields.Str()


def check_permission(permission):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user or not user.has_permission(permission):
        raise AuthorizationError(f'Permission required: {permission}')
    return user


def _generate_invoice_number():
    now = datetime.utcnow()
    prefix = now.strftime('INV-%Y%m')
    last = Invoice.query.filter(Invoice.invoice_number.like(f'{prefix}%')).order_by(Invoice.id.desc()).first()
    if last:
        seq = int(last.invoice_number.split('-')[-1]) + 1
    else:
        seq = 1
    return f'{prefix}-{seq:04d}'


@billing_bp.route('', methods=['GET'])
@jwt_required()
def list_invoices():
    check_permission('reports.read')

    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)
    status = request.args.get('status')
    ship_id = request.args.get('ship_id', type=int)
    search = request.args.get('search', '').strip()

    query = Invoice.query

    if status:
        try:
            query = query.filter(Invoice.status == InvoiceStatus(status))
        except ValueError:
            pass

    if ship_id:
        query = query.filter(Invoice.ship_id == ship_id)

    if search:
        query = query.filter(or_(
            Invoice.invoice_number.ilike(f'%{search}%'),
            Invoice.ship_name.ilike(f'%{search}%'),
        ))

    query = query.order_by(Invoice.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return success_response({
        'items': [inv.to_dict() for inv in pagination.items],
        'total': pagination.total,
        'page': pagination.page,
        'per_page': pagination.per_page,
        'pages': pagination.pages,
        'has_next': pagination.has_next,
        'has_prev': pagination.has_prev,
    })


@billing_bp.route('/<int:invoice_id>', methods=['GET'])
@jwt_required()
def get_invoice(invoice_id):
    check_permission('reports.read')
    invoice = Invoice.query.get(invoice_id)
    if not invoice:
        raise NotFoundError('Invoice not found')
    return success_response(invoice.to_dict())


@billing_bp.route('', methods=['POST'])
@jwt_required()
def create_invoice():
    user = check_permission('reports.write')

    try:
        data = InvoiceSchema().load(request.get_json() or {})
    except ValidationError as err:
        raise AppValidationError('Validation failed', details=err.messages)

    ship = Ship.query.get(data['ship_id'])
    if not ship:
        raise NotFoundError('Ship not found')

    berth = Berth.query.get(data['berth_id']) if data.get('berth_id') else None

    invoice = Invoice(
        invoice_number=_generate_invoice_number(),
        ship_id=data['ship_id'],
        ship_name=ship.name,
        berth_id=data.get('berth_id'),
        berth_name=berth.name if berth else None,
        billing_period_start=data['billing_period_start'],
        billing_period_end=data['billing_period_end'],
        tax_rate=data.get('tax_rate', 0),
        discount=data.get('discount', 0),
        due_date=data['due_date'],
        notes=data.get('notes'),
        terms=data.get('terms'),
        issued_by=user.id,
        status=InvoiceStatus.DRAFT,
    )
    db.session.add(invoice)
    db.session.flush()

    for li_data in data.get('line_items', []):
        line = BillingLine(
            invoice_id=invoice.id,
            category=BillingCategory(li_data['category']),
            description=li_data['description'],
            quantity=li_data.get('quantity', 1),
            unit=li_data.get('unit'),
            unit_price=li_data['unit_price'],
            amount=li_data.get('quantity', 1) * li_data['unit_price'],
            notes=li_data.get('notes'),
        )
        db.session.add(line)

    db.session.flush()
    invoice.calculate_totals()

    publish_event(
        event_type=EventType.INVOICE_CREATED,
        title=f'Invoice {invoice.invoice_number} created for {ship.name}',
        entity_type='invoice',
        entity_id=invoice.id,
        user_id=user.id,
        data={'invoice_number': invoice.invoice_number, 'total': invoice.total_amount},
    )

    db.session.commit()
    return success_response(invoice.to_dict(), 'Invoice created', 201)


@billing_bp.route('/<int:invoice_id>/lines', methods=['POST'])
@jwt_required()
def add_line_item(invoice_id):
    user = check_permission('reports.write')
    invoice = Invoice.query.get(invoice_id)
    if not invoice:
        raise NotFoundError('Invoice not found')
    if invoice.status not in [InvoiceStatus.DRAFT]:
        raise AppValidationError('Can only add lines to draft invoices')

    try:
        data = BillingLineSchema().load(request.get_json() or {})
    except ValidationError as err:
        raise AppValidationError('Validation failed', details=err.messages)

    line = BillingLine(
        invoice_id=invoice.id,
        category=BillingCategory(data['category']),
        description=data['description'],
        quantity=data.get('quantity', 1),
        unit=data.get('unit'),
        unit_price=data['unit_price'],
        amount=data.get('quantity', 1) * data['unit_price'],
        notes=data.get('notes'),
    )
    db.session.add(line)
    db.session.flush()
    invoice.calculate_totals()
    db.session.commit()

    return success_response(invoice.to_dict(), 'Line item added')


@billing_bp.route('/<int:invoice_id>/send', methods=['POST'])
@jwt_required()
def send_invoice(invoice_id):
    user = check_permission('reports.write')
    invoice = Invoice.query.get(invoice_id)
    if not invoice:
        raise NotFoundError('Invoice not found')
    if invoice.status != InvoiceStatus.DRAFT:
        raise AppValidationError('Only draft invoices can be sent')

    invoice.status = InvoiceStatus.SENT
    invoice.updated_at = datetime.utcnow()
    db.session.commit()

    publish_event(
        event_type=EventType.INVOICE_CREATED,
        title=f'Invoice {invoice.invoice_number} sent',
        entity_type='invoice',
        entity_id=invoice.id,
        user_id=user.id,
    )

    return success_response(invoice.to_dict(), 'Invoice sent')


@billing_bp.route('/<int:invoice_id>/pay', methods=['POST'])
@jwt_required()
def record_payment(invoice_id):
    user = check_permission('reports.write')
    invoice = Invoice.query.get(invoice_id)
    if not invoice:
        raise NotFoundError('Invoice not found')
    if invoice.status in [InvoiceStatus.CANCELLED, InvoiceStatus.REFUNDED]:
        raise AppValidationError('Cannot pay cancelled/refunded invoice')

    try:
        data = PaymentSchema().load(request.get_json() or {})
    except ValidationError as err:
        raise AppValidationError('Validation failed', details=err.messages)

    invoice.amount_paid = (invoice.amount_paid or 0) + data['amount']
    invoice.payment_method = PaymentMethod(data['payment_method'])
    invoice.payment_date = datetime.utcnow()
    invoice.payment_reference = data.get('payment_reference')
    invoice.balance_due = invoice.total_amount - invoice.amount_paid

    if invoice.balance_due <= 0:
        invoice.status = InvoiceStatus.PAID
        invoice.payment_status = 'Paid'
    else:
        invoice.status = InvoiceStatus.PARTIALLY_PAID
        invoice.payment_status = 'Partially Paid'

    invoice.updated_at = datetime.utcnow()
    db.session.commit()

    publish_event(
        event_type=EventType.INVOICE_PAID,
        title=f'Payment of {data["amount"]} recorded for {invoice.invoice_number}',
        entity_type='invoice',
        entity_id=invoice.id,
        user_id=user.id,
        severity=EventSeverity.INFO,
        data={'amount': data['amount'], 'method': data['payment_method']},
    )

    return success_response(invoice.to_dict(), 'Payment recorded')


@billing_bp.route('/<int:invoice_id>/cancel', methods=['POST'])
@jwt_required()
def cancel_invoice(invoice_id):
    user = check_permission('reports.write')
    invoice = Invoice.query.get(invoice_id)
    if not invoice:
        raise NotFoundError('Invoice not found')
    if invoice.status in [InvoiceStatus.PAID, InvoiceStatus.CANCELLED]:
        raise AppValidationError('Cannot cancel paid or already cancelled invoice')

    invoice.status = InvoiceStatus.CANCELLED
    invoice.updated_at = datetime.utcnow()
    db.session.commit()

    return success_response(invoice.to_dict(), 'Invoice cancelled')


@billing_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_billing_stats():
    check_permission('reports.read')

    total = Invoice.query.count()
    by_status = db.session.query(Invoice.status, func.count(Invoice.id)).group_by(Invoice.status).all()
    total_revenue = db.session.query(func.sum(Invoice.total_amount)).filter(
        Invoice.status.in_([InvoiceStatus.PAID, InvoiceStatus.PARTIALLY_PAID])
    ).scalar() or 0
    total_outstanding = db.session.query(func.sum(Invoice.balance_due)).filter(
        Invoice.status.in_([InvoiceStatus.SENT, InvoiceStatus.PARTIALLY_PAID, InvoiceStatus.OVERDUE])
    ).scalar() or 0
    total_collected = db.session.query(func.sum(Invoice.amount_paid)).scalar() or 0

    return success_response({
        'total': total,
        'by_status': {s.value: c for s, c in by_status},
        'total_revenue': round(total_revenue, 2),
        'total_outstanding': round(total_outstanding, 2),
        'total_collected': round(total_collected, 2),
    })


@billing_bp.route('/generate-berth-invoice', methods=['POST'])
@jwt_required()
def generate_berth_invoice():
    """Auto-generate invoice based on berth usage."""
    user = check_permission('reports.write')

    data = request.get_json() or {}
    ship_id = data.get('ship_id')
    berth_id = data.get('berth_id')

    if not ship_id:
        raise AppValidationError('ship_id required')

    ship = Ship.query.get(ship_id)
    if not ship:
        raise NotFoundError('Ship not found')

    berth = Berth.query.get(berth_id) if berth_id else None

    line_items = []
    base_rate = 5000  # per day
    crane_rate = 2000  # per crane-hour

    if ship.ata and ship.atd:
        days = max(1, (ship.atd - ship.ata).days)
    elif ship.ata:
        days = max(1, (datetime.utcnow() - ship.ata).days)
    else:
        days = 1

    line_items.append({
        'category': BillingCategory.BERTH_FEE.value,
        'description': f'Berth usage - {days} day(s)',
        'quantity': days,
        'unit': 'day',
        'unit_price': base_rate,
    })

    if berth and berth.has_crane:
        crane_hours = days * 8
        line_items.append({
            'category': BillingCategory.CONTAINER_HANDLING.value,
            'description': f'Crane operations - {crane_hours} hours',
            'quantity': crane_hours,
            'unit': 'hour',
            'unit_price': crane_rate,
        })

    line_items.append({
        'category': BillingCategory.PILOTAGE.value,
        'description': 'Pilotage services',
        'quantity': 1,
        'unit': 'service',
        'unit_price': 3000,
    })

    line_items.append({
        'category': BillingCategory.DOCUMENTATION.value,
        'description': 'Documentation and clearance',
        'quantity': 1,
        'unit': 'flat',
        'unit_price': 500,
    })

    now = datetime.utcnow()
    invoice = Invoice(
        invoice_number=_generate_invoice_number(),
        ship_id=ship.id,
        ship_name=ship.name,
        berth_id=berth.id if berth else None,
        berth_name=berth.name if berth else None,
        billing_period_start=ship.ata or now,
        billing_period_end=ship.atd or now,
        tax_rate=18.0,
        due_date=now.replace(day=min(28, now.day + 30)),
        issued_by=user.id,
        status=InvoiceStatus.DRAFT,
    )
    db.session.add(invoice)
    db.session.flush()

    for li in line_items:
        line = BillingLine(
            invoice_id=invoice.id,
            category=BillingCategory(li['category']),
            description=li['description'],
            quantity=li.get('quantity', 1),
            unit=li.get('unit'),
            unit_price=li['unit_price'],
            amount=li.get('quantity', 1) * li['unit_price'],
        )
        db.session.add(line)

    db.session.flush()
    invoice.calculate_totals()
    db.session.commit()

    publish_event(
        event_type=EventType.INVOICE_CREATED,
        title=f'Auto-generated invoice {invoice.invoice_number} for {ship.name}',
        entity_type='invoice',
        entity_id=invoice.id,
        user_id=user.id,
        data={'total': invoice.total_amount},
    )

    return success_response(invoice.to_dict(), 'Invoice generated', 201)
