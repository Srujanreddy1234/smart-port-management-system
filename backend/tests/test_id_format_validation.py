"""Every identifier field (ship_id, container_id, truck_number,
license_plate, berth_id/code, gate_code, incident_id, equipment_id)
used to accept any string up to a max length -- no actual format
check, so junk like "asdf!!" or mismatched-case IDs like the
"cont-100199" found in production could slip in. These lock in the
new format validators."""


def test_ship_id_rejects_bad_format_accepts_good(client, admin_headers):
    bad = client.post('/api/v1/ships', json={
        'ship_id': 'not a valid id!!', 'name': 'MV Test', 'vessel_type': 'Container Ship', 'flag': 'India',
    }, headers=admin_headers)
    assert bad.status_code == 400
    assert 'ship_id' in bad.get_json().get('details', bad.get_json().get('errors', {}))

    good = client.post('/api/v1/ships', json={
        'ship_id': 'SH-2026-0099', 'name': 'MV Test', 'vessel_type': 'Container Ship', 'flag': 'India',
    }, headers=admin_headers)
    assert good.status_code == 201, good.get_json()


def test_container_id_rejects_lowercase(client, admin_headers):
    # This is the exact real bug found in production: a container was
    # created as "cont-100199" while every other container follows
    # "CONT-NNNN" -- lowercase must now be rejected outright.
    res = client.post('/api/v1/containers', json={
        'container_id': 'cont-999999', 'container_type': '20ft',
    }, headers=admin_headers)
    assert res.status_code == 400


def test_truck_license_plate_format(client, admin_headers):
    bad = client.post('/api/v1/trucks', json={
        'truck_number': 'TN-9001', 'truck_type': 'Prime Mover', 'license_plate': 'not-a-plate',
    }, headers=admin_headers)
    assert bad.status_code == 400

    good = client.post('/api/v1/trucks', json={
        'truck_number': 'TN-9002', 'truck_type': 'Prime Mover', 'license_plate': 'TN-91-KX-4974',
    }, headers=admin_headers)
    assert good.status_code == 201, good.get_json()


def test_gate_code_format(client, admin_headers):
    bad = client.post('/api/v1/gates', json={
        'gate_code': '5', 'name': 'Bad Gate', 'gate_type': 'General / Mixed',
    }, headers=admin_headers)
    assert bad.status_code == 400

    good = client.post('/api/v1/gates', json={
        'gate_code': 'GATE-9', 'name': 'Good Gate', 'gate_type': 'General / Mixed',
    }, headers=admin_headers)
    assert good.status_code == 201, good.get_json()


def test_berth_code_and_id_format(client, admin_headers):
    bad = client.post('/api/v1/berths', json={
        'berth_id': 'berth!!', 'name': 'Bad Berth', 'code': 'b1',
    }, headers=admin_headers)
    assert bad.status_code == 400
