# HTTP boundary tests.
import pytest

from api import create_app
from api.errors import PublishError
from api.validation import utc_now

ENDPOINT = '/api/sensors/0001/readings'

class StubPublisher:
    """Records what was published, or fails on demand."""

    def __init__(self, error=None):
        self.published = []
        self._error = error

    def publish(self, reading):
        if self._error:
            raise self._error
        self.published.append(reading)

    def start(self):
        pass

    def close(self):
        pass

@pytest.fixture
def app(monkeypatch):
    def build(publisher=None):
        from api import publisher as publisher_module

        stub = publisher or StubPublisher()
        monkeypatch.setattr(publisher_module.Publisher, 'from_settings', classmethod(lambda cls, s: stub))
        instance = create_app()
        return instance, stub

    return build

# instead of using create_app() that tries to initiates a publisher with real paho connection, 
# use a StubPublisher
@pytest.fixture
def client(app):
    instance, _ = app()
    return instance.test_client()

def test_valid_reading_returns_202(app):
    instance, stub = app()
    response = instance.test_client().post(
        ENDPOINT, data={'value': '109', 'timestamp': str(utc_now())})

    assert response.status_code == 202
    assert response.get_json()['value'] == 109.0
    assert stub.published == [response.get_json()]

def test_invalid_reading_returns_400(client):
    response = client.post(ENDPOINT, data={'value': '999', 'timestamp': 'abc'})
    errors = response.get_json()['errors']

    assert response.status_code == 400
    assert {error['field'] for error in errors} == {'value', 'timestamp'}

def test_invalid_reading_is_never_published(app):
    instance, stub = app()
    instance.test_client().post(ENDPOINT, data={'value': '999', 'timestamp': str(utc_now())})
    
    assert stub.published == []

def test_broker_failure_returns_503_with_retry_after(app):
    instance, _ = app(StubPublisher(error=PublishError('broker unavailable')))
    response = instance.test_client().post(
        ENDPOINT, data={'value': '109', 'timestamp': str(utc_now())})

    assert response.status_code == 503
    assert response.headers['Retry-After'] == '5'

def test_missing_body_returns_400(client):
    assert client.post(ENDPOINT).status_code == 400

def test_non_post_method_is_rejected(client):
    assert client.get(ENDPOINT).status_code == 405
