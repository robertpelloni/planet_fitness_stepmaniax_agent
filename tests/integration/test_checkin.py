import pytest
from app import app
from models import db, User, Member, EquipmentMetric

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    with app.test_client() as client:
        with app.app_context():
            pass
        yield client

def test_hardware_checkin_nfc(client):
    """Test successful hardware check-in via NFC."""
    with app.app_context():
        # Setup test data
        member = Member(name="NFC Member", email="nfc@test.com", nfc_uid="nfc-123", registration_date="2026-05-01")
        unit = EquipmentMetric(equipment_name="SMX-1", location="Test Gym")
        admin = User(username='admin_checkin', role='Admin', api_key='checkin-key')
        admin.set_password('Admin123!')
        db.session.add_all([member, unit, admin])
        db.session.commit()
        unit_id = unit.id

    headers = {'X-API-KEY': 'checkin-key'}
    payload = {
        "nfc_uid": "nfc-123",
        "equipment_id": unit_id
    }
    response = client.post('/api/v1/telemetry/check-in', json=payload, headers=headers)
    assert response.status_code == 200
    data = response.get_json()
    assert data['member_name'] == "NFC Member"
    assert data['points_total'] == 1

def test_hardware_checkin_biometric(client):
    """Test successful hardware check-in via Biometric token."""
    with app.app_context():
        member = Member(name="Bio Member", email="bio@test.com", biometric_token="bio-token-456", registration_date="2026-05-01")
        unit = EquipmentMetric(equipment_name="SMX-2", location="Test Gym")
        admin = User(username='admin_checkin_2', role='Admin', api_key='checkin-key-2')
        admin.set_password('Admin123!')
        db.session.add_all([member, unit, admin])
        db.session.commit()
        unit_id = unit.id

    headers = {'X-API-KEY': 'checkin-key-2'}
    payload = {
        "biometric_token": "bio-token-456",
        "equipment_id": unit_id
    }
    response = client.post('/api/v1/telemetry/check-in', json=payload, headers=headers)
    assert response.status_code == 200
    assert response.get_json()['member_name'] == "Bio Member"
