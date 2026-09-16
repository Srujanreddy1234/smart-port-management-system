"""Shared marshmallow field validators for identifier-style fields.

Before this, every ID field across the API (ship_id, container_id,
truck_number, license_plate, gate_code, berth codes) only checked a
max length -- any string of the right length was accepted, including
mixed case and stray punctuation. One real consequence already in the
live data: a container was created as "cont-100199" (lowercase) while
every other container in the system follows "CONT-NNNN". These
validators enforce the uppercase, hyphen-separated convention the rest
of the system already uses, so new records can't drift from it.
"""
from marshmallow import validate

# General port asset identifier: SH-2023-0272, CONT-000161, TN-1227,
# GATE-1, BERTH-01 -- one leading letter, then uppercase letters,
# digits, and hyphens.
ASSET_ID_REGEX = r'^[A-Z][A-Z0-9-]{1,49}$'
ASSET_ID_MESSAGE = 'Must be uppercase letters, numbers, and hyphens only, starting with a letter (e.g. SH-2026-0001).'

# Indian vehicle registration format: TN-91-KX-4974 (state code, RTO
# code, series letters, registration number) -- this deployment is
# for a Tamil Nadu port, so real plates on real trucks will match this.
LICENSE_PLATE_REGEX = r'^[A-Z]{2}-\d{1,2}-[A-Z]{1,3}-\d{1,4}$'
LICENSE_PLATE_MESSAGE = 'Must be a valid registration number, e.g. TN-91-KX-4974.'

# Phone number: optional leading +, digits/spaces/hyphens only.
PHONE_REGEX = r'^\+?[\d\s-]{7,20}$'
PHONE_MESSAGE = 'Must be a valid phone number (digits, spaces, hyphens, optional leading +).'


def asset_id():
    return validate.Regexp(ASSET_ID_REGEX, error=ASSET_ID_MESSAGE)


def license_plate():
    return validate.Regexp(LICENSE_PLATE_REGEX, error=LICENSE_PLATE_MESSAGE)


def phone():
    return validate.Regexp(PHONE_REGEX, error=PHONE_MESSAGE)
