import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pytest
import base64
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['AUTH_USER'] = 'admin'
    app.config['AUTH_PASS'] = 'changeme'
    with app.test_client() as client:
        yield client

def get_auth_headers(username, password):
    return {
        'Authorization': 'Basic ' + base64.b64encode(f"{username}:{password}".encode('utf-8')).decode('utf-8')
    }

def test_index_unauthorized(client):
    rv = client.get('/')
    assert rv.status_code == 401

def test_index_authorized(client):
    # Depending on how app.py handles auth (it uses global constants currently, so we might need to match them)
    # in app.py: AUTH_USER = config.get(...)
    # We ideally want to mock valid credentials or just use the defaults associated with the code
    # Since we can't easily patch the global variables in app.py after import without reloading, 
    # we will use the default credentials that app.py loads from the default config logic or existing config.ini
    
    # Let's assume default "admin:changeme" or try to read what app.py has.
    from app import AUTH_USER, AUTH_PASS
    headers = get_auth_headers(AUTH_USER, AUTH_PASS)
    rv = client.get('/', headers=headers)
    assert rv.status_code == 200

def test_api_list_templates(client):
    from app import AUTH_USER, AUTH_PASS
    headers = get_auth_headers(AUTH_USER, AUTH_PASS)
    rv = client.get('/api/templates', headers=headers)
    assert rv.status_code == 200
    assert isinstance(rv.json, list)

def test_api_list_templates_snmp(client):
    from app import AUTH_USER, AUTH_PASS
    headers = get_auth_headers(AUTH_USER, AUTH_PASS)
    rv = client.get('/api/templates?type=snmp', headers=headers)
    assert rv.status_code == 200
    assert isinstance(rv.json, list)

def test_api_list_templates_invalid_type(client):
    from app import AUTH_USER, AUTH_PASS
    headers = get_auth_headers(AUTH_USER, AUTH_PASS)
    rv = client.get('/api/templates?type=invalid', headers=headers)
    assert rv.status_code == 400
