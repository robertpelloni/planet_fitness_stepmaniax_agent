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
            db.drop_all()
            db.create_all()
        yield client

def test_live_occupancy_api(client):
    """Test the live occupancy analytics endpoint."""
    with app.app_context():
        unit = EquipmentMetric(equipment_name="Test Unit", location="Test Loc", uptime_percent=100.0)
        db.session.add(unit)
        db.session.commit()
        unit_id = unit.id

        scan = TelemetryHistory(
            equipment_id=unit_id,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            scans_count=5
        )
        db.session.add(scan)
        db.session.commit()

        import secrets
        test_key = secrets.token_urlsafe(32)
        admin = User(username='admin_live', role='Admin', api_key=test_key)
        admin.set_password('Admin123!')
        db.session.add(admin)
        db.session.commit()

    headers = {'X-API-KEY': test_key}
    response = client.get('/api/v1/analytics/live-occupancy', headers=headers)
    assert response.status_code == 200
    data = response.get_json()

    assert data['total_active_scans'] == 5
    assert data['units'][0]['intensity'] == 0.5
