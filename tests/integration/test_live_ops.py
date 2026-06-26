import pytest
from app import app
from models import db, User, EquipmentMetric, TelemetryHistory
from datetime import datetime, timedelta

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    with app.test_client() as client:
        with app.app_context():
            pass
        yield client

def test_live_occupancy_api(client):
    """Test the live occupancy analytics endpoint."""
    with app.app_context():
        # Setup test unit and recent scan
        unit = EquipmentMetric(equipment_name="Test Unit", location="Test Loc", uptime_percent=100.0)
        db.session.add(unit)
        db.session.commit()
        unit_id = unit.id

        # Add a scan in the last 5 minutes
        scan = TelemetryHistory(
            equipment_id=unit_id,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            scans_count=5
        )
        db.session.add(scan)

        # Add a scan older than 15 minutes
        old_scan = TelemetryHistory(
            equipment_id=unit_id,
            timestamp=(datetime.now() - timedelta(minutes=20)).strftime("%Y-%m-%d %H:%M:%S"),
            scans_count=10
        )
        db.session.add(old_scan)
        db.session.commit()

    # Authenticate (using admin from populate_test_data if available or mock)
    # For unit test, we can use require_api_key check if we provide a key
    with app.app_context():
        admin = User(username='admin_live', role='Admin', api_key='live-key')
        admin.set_password('Admin123!')
        db.session.add(admin)
        db.session.commit()

    headers = {'X-API-KEY': 'live-key'}
    response = client.get('/api/v1/analytics/live-occupancy', headers=headers)
    assert response.status_code == 200
    data = response.get_json()

    assert data['total_active_scans'] >= 5 # Only the recent scan
    test_unit = next(u for u in data['units'] if u['name'] == 'Test Unit')
    assert test_unit['intensity'] == 0.5 # 5 scans / 10.0 scale
