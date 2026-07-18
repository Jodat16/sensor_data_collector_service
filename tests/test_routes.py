# HTTP boundary tests.
import pytest

from api import create_app
from api.validation import utc_now

ENDPOINT = '/api/sensors/0001/readings'

@pytest.fixture
def client():
    return create_app().test_client()

def test_valid_reading_returns_200(client):
    response = client.post(ENDPOINT, data={'value': '109', 'timestamp': str(utc_now())})
    body = response.get_json()

    assert response.status_code == 200
    assert body == {'device_id': '0001', 'value': 109.0, 'timestamp': pytest.approx(utc_now(), abs=10)}
    assert isinstance(body['value'], float)

def test_invalid_reading_returns_400(client):
    response = client.post(ENDPOINT, data={'value': '999', 'timestamp': 'abc'})
    errors = response.get_json()['errors']

    assert response.status_code == 400
    assert {error['field'] for error in errors} == {'value', 'timestamp'}
    assert all(error['reason'] for error in errors)

def test_missing_body_returns_400(client):
    assert client.post(ENDPOINT).status_code == 400

def test_non_post_method_is_rejected(client):
    assert client.get(ENDPOINT).status_code == 405
