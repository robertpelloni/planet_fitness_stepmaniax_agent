import pytest
from app import app
from models import db, User

def test_unified_dashboard_access():
    with app.test_client() as client:
        with app.app_context():
            admin_user = User.query.filter_by(role='Admin').first()
            assert admin_user is not None
        with client.session_transaction() as sess:
            sess['_user_id'] = str(admin_user.id)
            sess['_fresh'] = True

        response = client.get('/admin/unified-dashboard')
        assert response.status_code == 200
        html = response.data.decode('utf-8')
        assert "Global Operations Center" in html
        assert "Enterprise Franchise Pipeline" in html
        assert "Hardware Telemetry &amp; Fleet Operations" in html
        assert "Pilot Financials &amp; ROI Benchmark" in html
        assert "Live Daemon Activity Stream" in html
