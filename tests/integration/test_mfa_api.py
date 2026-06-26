import pytest
from app import app
from models import db, User
import pyotp

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    with app.test_client() as client:
        with app.app_context():
            pass
        yield client

def test_mfa_login_sequence(client):
    """Test the login flow for an MFA-enabled user."""
    with app.app_context():
        # Create a user with MFA enabled
        mfa_user = User(username='mfa_test', mfa_secret=pyotp.random_base32(), mfa_enabled=True)
        mfa_user.set_password('Admin123!')
        db.session.add(mfa_user)
        db.session.commit()
        user_id = mfa_user.id

    # 1. First step login
    response = client.post('/login', data={'username': 'mfa_test', 'password': 'Admin123!'}, follow_redirects=True)
    assert b"Two-Factor Authentication" in response.data

    # 2. MFA Verification
    with client.session_transaction() as sess:
        assert sess['mfa_user_id'] == user_id

    with app.app_context():
        user = User.query.get(user_id)
        totp = pyotp.TOTP(user.mfa_secret)
        token = totp.now()

    response = client.post('/login/2fa', data={'token': token}, follow_redirects=True)
    assert b"COMMAND CENTER" in response.data or b"Staff Portal" in response.data or b"Portfolio" in response.data

def test_per_user_api_key(client):
    """Test API key validation using per-user keys."""
    with app.app_context():
        test_user = User(username='api_test', api_key='test-key-123')
        test_user.set_password('Admin123!')
        db.session.add(test_user)
        db.session.commit()

    # Unauthorized access
    response = client.get('/api/v1/enterprise/export')
    assert response.status_code == 401

    # Authorized access with user-specific key
    headers = {'X-API-KEY': 'test-key-123'}
    response = client.get('/api/v1/enterprise/export', headers=headers)
    assert response.status_code == 200
    assert response.get_json()['version'] == '4.8.1'
