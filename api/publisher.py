# REQ-2 -- publish validated readings to the MQTT broker

import json
import logging
import paho.mqtt.client as mqtt

from .errors import PublishError

logger = logging.getLogger(__name__)

class Publisher:
    def __init__(self, host, port, topic, qos=1, keepalive=60, publish_timeout=5.0,
                 client_id='', username=None, password=None, tls=False):
        self.host = host
        self.port = port
        self.topic = topic
        self.qos = qos
        self.keepalive = keepalive
        self.publish_timeout = publish_timeout

        self._client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=client_id)

        if username:
            self._client.username_pw_set(username, password)
        if tls:
            self._client.tls_set()

    @classmethod
    def from_settings(cls, settings):
        """Build from configuration."""
        return cls(
            host=settings.MQTT_HOST,
            port=settings.MQTT_PORT,
            topic=settings.BROKER_TOPIC,
            qos=settings.MQTT_QOS,
            keepalive=settings.MQTT_KEEPALIVE,
            publish_timeout=settings.MQTT_PUBLISH_TIMEOUT,
            client_id=settings.MQTT_CLIENT_ID,
            username=settings.MQTT_USERNAME,
            password=settings.MQTT_PASSWORD,
            tls=settings.MQTT_TLS,
        )

    def start(self):
        """Connect in the background and start paho's network loop.

        connect_async rather than connect: a broker that is down must not stop
        the service from starting. Readings are refused with 503 until the
        connection is up, and paho reconnects on its own.
        """
        self._client.connect_async(self.host, self.port, keepalive=self.keepalive)
        self._client.loop_start()
        logger.info('mqtt publisher started host=%s port=%s topic=%s', self.host, self.port, self.topic)

    def publish(self, reading):
        """Publish a reading and wait for the broker to confirm it."""
        payload = json.dumps(reading, separators=(',', ':'))
        #retain last message on the broker for the new subscriber
        message = self._client.publish(self.topic, payload, qos=self.qos, retain=True)

        if message.rc != mqtt.MQTT_ERR_SUCCESS:
            logger.error('publish rejected device_id=%s rc=%s', reading['device_id'], message.rc)
            raise PublishError(f'broker did not accept the reading (rc={message.rc})')

        try:
            # QoS-1, waits for response from broker, not ust fire and forget
            message.wait_for_publish(timeout=self.publish_timeout)
        except (ValueError, RuntimeError) as error:
            logger.error('publish unconfirmed device_id=%s: %s', reading['device_id'], error)
            raise PublishError('broker did not confirm the reading in time') from error

    def close(self):
        self._client.loop_stop()
        self._client.disconnect()
        logger.info('mqtt publisher stopped')
