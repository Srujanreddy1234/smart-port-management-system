#!/usr/bin/env python3
"""Migrate enum storage from NAMES to VALUES in smart_port.db."""
import os
import sqlite3

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'smart_port.db')

mappings = {
    'ships': {
        'vessel_type': {
            'CONTAINER_SHIP': 'Container Ship', 'BULK_CARRIER': 'Bulk Carrier', 'TANKER': 'Tanker',
            'RO_RO': 'Ro-Ro', 'GENERAL_CARGO': 'General Cargo', 'FISHING': 'Fishing Vessel',
            'TUG': 'Tug Boat', 'PILOT_BOAT': 'Pilot Boat', 'BARGE': 'Barge', 'OTHER': 'Other',
        },
        'status': {
            'SCHEDULED': 'Scheduled', 'APPROACHING': 'Approaching', 'IN_CHANNEL': 'In Channel',
            'ANCHORED': 'Anchored', 'AT_BERTH': 'At Berth', 'LOADING': 'Loading',
            'UNLOADING': 'Unloading', 'DEPARTING': 'Departing', 'DEPARTED': 'Departed',
            'DIVERTED': 'Diverted', 'DELAYED': 'Delayed',
        },
    },
    'containers': {
        'status': {
            'AT_PORT': 'At Port', 'CUSTOMS_HOLD': 'Customs Hold', 'DAMAGED': 'Damaged',
            'LOADED': 'Loaded', 'EMPTY': 'Empty', 'IN_TRANSIT': 'In Transit',
            'RELEASED': 'Released', 'DESTROYED': 'Destroyed',
        },
        'container_type': {
            'TWENTY_FT': '20ft Dry', 'FORTY_FT': '40ft Dry', 'FORTY_FT_HC': '40ft High Cube',
            'REEFER': '20ft Reefer', 'FORTY_FT_REEFER': '40ft Reefer', 'FLAT_RACK': 'Flat Rack',
            'OPEN_TOP': 'Open Top', 'TANK': 'Tank', 'OTHER': 'Other',
        },
    },
    'trucks': {
        'status': {
            'AVAILABLE': 'Available', 'ASSIGNED': 'Assigned', 'LOADING': 'Loading',
            'UNLOADING': 'Unloading', 'IN_TRANSIT': 'In Transit', 'OFFLINE': 'Offline',
            'WAITING': 'Waiting', 'MAINTENANCE': 'Maintenance',
        },
        'truck_type': {
            'CHASSIS': 'Chassis', 'FORKLIFT': 'Forklift', 'EMPTY_HANDLER': 'Empty Handler', 'OTHER': 'Other',
        },
    },
    'berths': {
        'status': {
            'AVAILABLE': 'Available', 'OCCUPIED': 'Occupied', 'MAINTENANCE': 'Maintenance',
            'RESERVED': 'Reserved', 'OUT_OF_SERVICE': 'Out of Service',
        },
    },
}

conn = sqlite3.connect(DB)
cur = conn.cursor()

for table, columns in mappings.items():
    for column, mapping in columns.items():
        for name, value in mapping.items():
            cur.execute(f'UPDATE {table} SET {column} = ? WHERE {column} = ?', (value, name))
        print(f'  {table}.{column}: migrated {len(mapping)} mappings')

conn.commit()
conn.close()
print('Done.')
