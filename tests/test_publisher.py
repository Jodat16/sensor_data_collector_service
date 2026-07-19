# REQ-2 unit test
#
# Proves the publisher hands the broker a well-formed payload. It cannot prove a
# reading actually arrives - only an integration test against a real broker
# does that.

import json
import paho.mqtt.client as mqtt
import pytest

from api.publisher import Publisher

READING = {'device_id': '0001', 'value': 109.0, 'timestamp': 1752243577}

class FakeClient:
    """Acts as a paho's mqtt client, recording what the publisher asked of it."""

    def __init__(self):
        self.published = []

    def username_pw_set(self, username, password):
        pass

    def tls_set(self):
        pass

    def publish(self, topic, payload, qos, retain):
        self.published.append({'topic': topic, 'payload': payload, 'qos': qos, 'retain': retain})
        return type('MessageInfo', (), {
            'rc': mqtt.MQTT_ERR_SUCCESS,
            'wait_for_publish': lambda self, timeout=None: None,
        })()

@pytest.fixture
def publisher(monkeypatch):
    client = FakeClient()
    monkeypatch.setattr(mqtt, 'Client', lambda *args, **kwargs: client)
    return Publisher(host='localhost', port=1883, topic='service/secom/data01', qos=1), client

def test_publishes_the_reading_as_json_with_typed_fields(publisher):
    """The payload must be valid JSON carrying all three fields at the right types."""
    instance, client = publisher

    instance.publish(READING)
    payload = json.loads(client.published[0]['payload'])

    assert payload == READING
    assert isinstance(payload['value'], float)
    assert isinstance(payload['timestamp'], int)
    assert isinstance(payload['device_id'], str)
