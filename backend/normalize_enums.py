#!/usr/bin/env python3
"""Normalize enum storage in smart_port.db: convert enum VALUES back to enum NAMES.

SQLAlchemy's Enum(PythonEnum) stores the enum NAME (e.g. 'CONTAINER_SHIP') by default.
Some rows were seeded with the VALUE (e.g. 'Container Ship') which breaks lookups.
"""
import sqlite3
import os

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'smart_port.db')
conn = sqlite3.connect(DB)
cur = conn.cursor()

# name -> value maps (reverse of what we need)
ship_vessel = {
    'CONTAINER_SHIP': 'Container Ship',
    'BULK_CARRIER': 'Bulk Carrier',
    'TANKER': 'Tanker',
    'RO_RO': 'Ro-Ro',
    'GENERAL_CARGO': 'General Cargo',
    'FISHING': 'Fishing Vessel',
    'TUG': 'Tug Boat',
    'PILOT_BOAT': 'Pilot Boat',
    'BARGE': 'Barge',
    'OTHER': 'Other',
}
ship_status = {
    'SCHEDULED': 'Scheduled', 'APPROACHING': 'Approaching', 'IN_CHANNEL': 'In Channel',
    'ANCHORED': 'Anchored', 'AT_BERTH': 'At Berth', 'LOADING': 'Loading',
    'UNLOADING': 'Unloading', 'DEPARTING': 'Departing', 'DEPARTED': 'Departed',
    'DIVERTED': 'Diverted', 'DELAYED': 'Delayed',
}
container_status = {
    'AT_PORT': 'At Port', 'CUSTOMS_HOLD': 'Customs Hold', 'DAMAGED': 'Damaged',
    'LOADED': 'Loaded', 'EMPTY': 'Empty', 'IN_TRANSIT': 'In Transit',
    'RELEASED': 'Released', 'DESTROYED': 'Destroyed',
}
container_type = {
    'TWENTY_FT': '20ft Dry', 'FORTY_FT': '40ft Dry', 'FORTY_FT_HC': '40ft High Cube',
    'REEFER': '20ft Reefer', 'FORTY_FT_REEFER': '40ft Reefer', 'FLAT_RACK': 'Flat Rack',
    'OPEN_TOP': 'Open Top', 'TANK': 'Tank', 'OTHER': 'Other',
}
truck_status = {
    'AVAILABLE': 'Available', 'ASSIGNED': 'Assigned', 'LOADING': 'Loading',
    'UNLOADING': 'Unloading', 'IN_TRANSIT': 'In Transit', 'OFFLINE': 'Offline',
    'WAITING': 'Waiting', 'MAINTENANCE': 'Maintenance',
}
truck_type = {'CHASSIS': 'Chassis', 'FORKLIFT': 'Forklift', 'EMPTY_HANDLER': 'Empty Handler', 'OTHER': 'Other'}
berth_status = {
    'AVAILABLE': 'Available', 'OCCUPIED': 'Occupied', 'MAINTENANCE': 'Maintenance',
    'RESERVED': 'Reserved', 'OUT_OF_SERVICE': 'Out of Service',
}

def fix(table, column, mapping):
    for name, value in mapping.items():
        cur.execute(f'UPDATE {table} SET {column} = ? WHERE {column} = ?', (name, value))
    # Also ensure any remaining values not in mapping are untouched
    print(f'  {table}.{column}: checked {len(mapping)} mappings')

print('Normalizing enum VALUES -> NAMES:')
fix('ships', 'vessel_type', ship_vessel)
fix('ships', 'status', ship_status)
fix('containers', 'status', container_status)
fix('containers', 'container_type', container_type)
fix('trucks', 'status', truck_status)
fix('trucks', 'truck_type', truck_type)
cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='berths'")
if cur.fetchone():
    fix('berths', 'status', berth_status)

conn.commit()
conn.close()
print('Done.')