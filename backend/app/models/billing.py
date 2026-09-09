from datetime import datetime
from enum import Enum as PyEnum
from app.extensions import db
from sqlalchemy import Enum, Index, ForeignKey
from sqlalchemy.orm import relationship


class InvoiceStatus(PyEnum):
    DRAFT = 'Draft'
    SENT = 'Sent'
    PAID = 'Paid'
    PARTIALLY_PAID = 'Partially Paid'
    OVERDUE = 'Overdue'
    CANCELLED = 'Cancelled'
    REFUNDED = 'Refunded'


class PaymentMethod(PyEnum):
    BANK_TRANSFER = 'Bank Transfer'
    CREDIT_CARD = 'Credit Card'
    CHEQUE = 'Cheque'
    CASH = 'Cash'
    ONLINE = 'Online Payment'


class BillingCategory(PyEnum):
    BERTH_FEE = 'Berth Usage Fee'
    PILOTAGE = 'Pilotage Fee'
    TUGGING = 'Tugging Fee'
    MOORING = 'Mooring Fee'
    CONTAINER_HANDLING = 'Container Handling'
    STORAGE = 'Storage Fee'
    DOCUMENTATION = 'Documentation Fee'
    INSPECTION = 'Inspection Fee'
    ENVIRONMENTAL = 'Environmental Fee'
    SECURITY = 'Security Fee'
    EQUIPMENT_RENTAL = 'Equipment Rental'
    LABOR = 'Labor Charges'
    OTHER = 'Other'


class Invoice(db.Model):
    __tablename__ = 'invoices'

    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    ship_id = db.Column(db.Integer, db.ForeignKey('ships.id'), index=True)
    ship_name = db.Column(db.String(255))
    berth_id = db.Column(db.Integer, db.ForeignKey('berths.id'), index=True)
    berth_name = db.Column(db.String(255))
    billing_period_start = db.Column(db.DateTime)
    billing_period_end = db.Column(db.DateTime)
    subtotal = db.Column(db.Float, default=0)
    tax_rate = db.Column(db.Float, default=0)
    tax_amount = db.Column(db.Float, default=0)
    discount = db.Column(db.Float, default=0)
    total_amount = db.Column(db.Float, default=0)
    amount_paid = db.Column(db.Float, default=0)
    balance_due = db.Column(db.Float, default=0)
    status = db.Column(Enum(InvoiceStatus, values_callable=lambda enum_cls: [e.value for e in enum_cls]), default=InvoiceStatus.DRAFT, nullable=False, index=True)
    payment_status = db.Column(db.String(50), default='Unpaid')
    payment_method = db.Column(Enum(PaymentMethod, values_callable=lambda enum_cls: [e.value for e in enum_cls]))
    payment_date = db.Column(db.DateTime)
    payment_reference = db.Column(db.String(100))
    due_date = db.Column(db.DateTime, index=True)
    notes = db.Column(db.Text)
    terms = db.Column(db.Text)
    issued_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    ship = relationship('Ship', backref='invoices')
    berth = relationship('Berth', backref='invoices')
    issuer = relationship('User', foreign_keys=[issued_by], backref='issued_invoices')
    line_items = relationship('BillingLine', backref='invoice', cascade='all, delete-orphan')

    __table_args__ = (
        Index('ix_invoice_status_date', 'status', 'created_at'),
        Index('ix_invoice_ship_date', 'ship_id', 'created_at'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'invoice_number': self.invoice_number,
            'ship_id': self.ship_id,
            'ship_name': self.ship_name,
            'berth_id': self.berth_id,
            'berth_name': self.berth_name,
            'billing_period_start': self.billing_period_start.isoformat() if self.billing_period_start else None,
            'billing_period_end': self.billing_period_end.isoformat() if self.billing_period_end else None,
            'subtotal': self.subtotal,
            'tax_rate': self.tax_rate,
            'tax_amount': self.tax_amount,
            'discount': self.discount,
            'total_amount': self.total_amount,
            'amount_paid': self.amount_paid,
            'balance_due': self.balance_due,
            'status': self.status.value,
            'payment_status': self.payment_status,
            'payment_method': self.payment_method.value if self.payment_method else None,
            'payment_date': self.payment_date.isoformat() if self.payment_date else None,
            'payment_reference': self.payment_reference,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'notes': self.notes,
            'terms': self.terms,
            'issued_by': self.issued_by,
            'line_items': [li.to_dict() for li in self.line_items],
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

    def calculate_totals(self):
        self.subtotal = sum(li.amount for li in self.line_items)
        self.tax_amount = self.subtotal * (self.tax_rate / 100) if self.tax_rate else 0
        self.total_amount = self.subtotal + self.tax_amount - (self.discount or 0)
        self.balance_due = self.total_amount - (self.amount_paid or 0)


class BillingLine(db.Model):
    __tablename__ = 'billing_lines'

    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=False, index=True)
    category = db.Column(Enum(BillingCategory, values_callable=lambda enum_cls: [e.value for e in enum_cls]), nullable=False, index=True)
    description = db.Column(db.String(500), nullable=False)
    quantity = db.Column(db.Float, default=1)
    unit = db.Column(db.String(50))
    unit_price = db.Column(db.Float, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index('ix_billing_line_invoice', 'invoice_id'),
        Index('ix_billing_line_category', 'category'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'invoice_id': self.invoice_id,
            'category': self.category.value,
            'description': self.description,
            'quantity': self.quantity,
            'unit': self.unit,
            'unit_price': self.unit_price,
            'amount': self.amount,
            'notes': self.notes,
            'created_at': self.created_at.isoformat()
        }
