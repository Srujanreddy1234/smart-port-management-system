#!/usr/bin/env python3
"""Repair enum columns in smart_port.db so every stored value matches a model enum VALUE.

The database was seeded with a mix of enum member NAMES (e.g. 'INTRUSION', 'PAID',
'AT_GATE') and legacy display strings (e.g. '20ft Dry', '40ft High Cube'). SQLAlchemy's
``Enum(EnumClass, values_callable=...)`` validates rows against the enum *values*, so
any mismatched row raises a LookupError and breaks the affected endpoint with a 500.

This script is idempotent: it only rewrites values that are not already a valid enum
value.  Run from the backend directory:

    python fix_enums.py
"""
import os
import sqlite3

os.environ.setdefault('FLASK_ENV', 'development')

from app import create_app
from app.extensions import db
from app.models.container import ContainerType, ContainerStatus
from app.models.truck import TruckType, TruckStatus
from app.models.ship import VesselType, ShipStatus, BerthStatus
from app.models.billing import InvoiceStatus, PaymentMethod, BillingCategory
from app.models.security import (
    IncidentType, IncidentSeverity, IncidentStatus, SecurityZone, AlertType,
)
from app.models.maintenance import (
    EquipmentType, EquipmentStatus, MaintenanceType, MaintenancePriority,
    MaintenanceStatus,
)
from app.models.event_log import EventType, EventSeverity
from app.models.reports import ReportType, ReportFormat, ReportStatus, ReportSchedule
from app.models.user import UserRole, UserStatus

# Legacy aliases: stored_value -> correct enum VALUE.
# Covers historical seed data that used display strings instead of enum names/values.
LEGACY = {
    ('containers', 'container_type'): {
        '20ft Dry': '20ft', '20ft Reefer': 'Reefer', '40ft Dry': '40ft',
        '40ft High Cube': '40ft HC', 'HAZMAT': 'Hazmat',
    },
    ('containers', 'status'): {
        'DELIVERED': 'Delivered', 'LOST': 'Lost',
    },
    ('trucks', 'status'): {'AT_GATE': 'At Gate'},
    ('trucks', 'truck_type'): {
        'PRIME_MOVER': 'Prime Mover', 'REACH_STACKER': 'Reach Stacker',
        'TRAILER': 'Trailer',
    },
    ('invoices', 'status'): {'PAID': 'Paid'},
    ('invoices', 'payment_method'): {'BANK_TRANSFER': 'Bank Transfer'},
    ('security_incidents', 'incident_type'): {
        'INTRUSION': 'Intrusion', 'SUSPICIOUS_ACTIVITY': 'Suspicious Activity',
    },
    ('security_incidents', 'severity'): {'HIGH': 'High', 'MEDIUM': 'Medium'},
    ('security_incidents', 'status'): {
        'ACTIVE': 'Active', 'INVESTIGATING': 'Investigating',
    },
    ('security_incidents', 'zone'): {'ZONE_B': 'Zone B - Berth 4-6', 'ZONE_C': 'Zone C - Gate 1-2'},
    ('equipment', 'equipment_type'): {
        'CRANE_RTG': 'RTG Crane', 'CRANE_STS': 'Ship-to-Shore Crane',
        'REACH_STACKER': 'Reach Stacker',
    },
    ('equipment', 'status'): {'OPERATIONAL': 'Operational'},
    ('event_logs', 'event_type'): {
        'BERTH_ASSIGNMENT': 'Berth Assignment', 'BERTH_RELEASE': 'Berth Release',
        'INVOICE_CREATED': 'Invoice Created', 'INVOICE_PAID': 'Invoice Paid',
        'TRUCK_GATE_IN': 'Truck Gate In', 'TRUCK_GATE_OUT': 'Truck Gate Out',
    },
    ('reports', 'report_type'): {'VESSEL_TRAFFIC': 'Vessel Traffic'},
    ('reports', 'status'): {'READY': 'Ready'},
    ('billing_lines', 'category'): {
        'BERTH_FEE': 'Berth Usage Fee', 'DOCUMENTATION': 'Documentation Fee',
        'PILOTAGE': 'Pilotage Fee',
    },
    ('reports', 'schedule'): {'ON_DEMAND': 'On Demand'},
}

# (table, column, enum_class) pairs to normalize.
TARGETS = [
    ('containers', 'container_type', ContainerType),
    ('containers', 'status', ContainerStatus),
    ('ships', 'vessel_type', VesselType),
    ('ships', 'status', ShipStatus),
    ('trucks', 'truck_type', TruckType),
    ('trucks', 'status', TruckStatus),
    ('berths', 'status', BerthStatus),
    ('invoices', 'status', InvoiceStatus),
    ('invoices', 'payment_method', PaymentMethod),
    ('security_incidents', 'incident_type', IncidentType),
    ('security_incidents', 'severity', IncidentSeverity),
    ('security_incidents', 'status', IncidentStatus),
    ('security_incidents', 'zone', SecurityZone),
    ('alerts', 'alert_type', AlertType),
    ('alerts', 'severity', IncidentSeverity),
    ('alerts', 'zone', SecurityZone),
    ('equipment', 'equipment_type', EquipmentType),
    ('equipment', 'status', EquipmentStatus),
    ('maintenance_schedules', 'maintenance_type', MaintenanceType),
    ('maintenance_schedules', 'priority', MaintenancePriority),
    ('maintenance_schedules', 'status', MaintenanceStatus),
    ('event_logs', 'event_type', EventType),
    ('event_logs', 'severity', EventSeverity),
    ('reports', 'report_type', ReportType),
    ('reports', 'format', ReportFormat),
    ('reports', 'status', ReportStatus),
    ('reports', 'schedule', ReportSchedule),
    ('billing_lines', 'category', BillingCategory),
    ('users', 'role', UserRole),
    ('users', 'status', UserStatus),
]


def build_mapping(enum_cls):
    """Return {stored_value: correct_value} for an enum class.

    Includes every member name and every member value as a source key.
    """
    mapping = {}
    for member in enum_cls:
        mapping[member.name] = member.value      # enum NAME -> value
        mapping[member.value] = member.value     # already-correct value (no-op)
    return mapping


def main():
    app = create_app('development')
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'smart_port.db')
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    total_fixed = 0
    for table, column, enum_cls in TARGETS:
        # Verify the column exists (schema may differ from model).
        cur.execute(f"PRAGMA table_info('{table}')")
        cols = [r[1] for r in cur.fetchall()]
        if column not in cols:
            print(f"  SKIP {table}.{column} (column missing)")
            continue

        mapping = build_mapping(enum_cls)
        mapping.update(LEGACY.get((table, column), {}))

        cur.execute(f"SELECT DISTINCT {column} FROM {table}")
        stored_values = [r[0] for r in cur.fetchall() if r[0] is not None]

        for stored in stored_values:
            correct = mapping.get(stored)
            if correct is None or correct == stored:
                continue
            cur.execute(
                f"UPDATE {table} SET {column} = ? WHERE {column} = ?",
                (correct, stored),
            )
            total_fixed += cur.rowcount
            print(f"  {table}.{column}: '{stored}' -> '{correct}' ({cur.rowcount} rows)")

    conn.commit()
    conn.close()

    print(f"\nTotal enum values repaired: {total_fixed}")


if __name__ == '__main__':
    main()