import pytest
from app import app
from config import API_KEY

@pytest.fixture
def client():
    app.config['TESTING'] = True
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
    """Test successful enterprise data export with API key."""
    headers = {'X-API-KEY': API_KEY}
    response = client.get('/api/v1/enterprise/export', headers=headers)
    assert response.status_code == 200
    data = response.get_json()
    assert "telemetry" in data
    assert "engagement" in data
    assert "sentiment" in data
    assert data["version"] == "4.8.0"

def test_enterprise_leads_success(client):
    """Test successful enterprise lead sync with API key."""
    headers = {'X-API-KEY': API_KEY}
    response = client.get('/api/v1/enterprise/leads', headers=headers)
    assert response.status_code == 200
    data = response.get_json()
    assert "leads" in data
    assert "count" in data
