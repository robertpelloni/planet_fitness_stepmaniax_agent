import pytest
from app import app
from config import API_KEY

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    with app.test_client() as client:
        yield client

def test_enterprise_export_unauthorized(client):
    """Test that enterprise export fails without API key."""
    response = client.get('/api/v1/enterprise/export')
    assert response.status_code == 401

def test_enterprise_leads_unauthorized(client):
    """Test that enterprise leads fails without API key."""
    response = client.get('/api/v1/enterprise/leads')
    assert response.status_code == 401

def test_enterprise_export_success(client):
    """Test successful enterprise data export with API key and dynamic MET estimation."""
    headers = {'X-API-KEY': API_KEY}
    response = client.get('/api/v1/enterprise/export', headers=headers)
    assert response.status_code == 200
    data = response.get_json()
    assert "telemetry" in data
    assert "engagement" in data
    assert "sentiment" in data
    assert data["version"] == "9.5.0"
    assert "pilot_session_logs" in data
    assert len(data["telemetry"]) > 0
    # Ensure dynamic MET calculation is present and populated
    first_unit = data["telemetry"][0]
    assert "estimated_met_capacity" in first_unit
    assert isinstance(first_unit["estimated_met_capacity"], (int, float))
    assert first_unit["estimated_met_capacity"] > 0

def test_enterprise_export_csv_format(client):
    """Test enterprise export returning CSV formatted attachment."""
    headers = {'X-API-KEY': API_KEY}
    response = client.get('/api/v1/enterprise/export?format=csv', headers=headers)
    assert response.status_code == 200
    assert "text/csv" in response.content_type
    assert "attachment; filename=enterprise_telemetry_export.csv" in response.headers.get("Content-Disposition", "")
    csv_text = response.get_data(as_text=True)
    assert "Unit ID,Name,Location,Uptime %,Total Scans,Avg Session (min),Estimated MET Capacity,Health Score,Status" in csv_text

def test_enterprise_leads_success(client):
    """Test successful enterprise lead sync with API key."""
    headers = {'X-API-KEY': API_KEY}
    response = client.get('/api/v1/enterprise/leads', headers=headers)
    assert response.status_code == 200
    data = response.get_json()
    assert "leads" in data
    assert "count" in data
