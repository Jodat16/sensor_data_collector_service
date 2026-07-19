from environs import Env

env = Env()
env.read_env()

DEBUG = env.bool("FLASK_DEBUG", default=False)
SECRET_KEY = env.str("FLASK_SECRET_KEY")

LOG_LEVEL = env.str("LOG_LEVEL", default="WARNING")

HOST = env.str("FLASK_HOST", default="127.0.0.1")
PORT = env.int("FLASK_PORT", default=5000)

BROKER_TOPIC = env.str("BROKER_TOPIC", default="service/secom/data01")

# MQTT Broker Config
MQTT_HOST = env.str("MQTT_HOST", default="localhost")
MQTT_PORT = env.int("MQTT_PORT", default=1883)
MQTT_USERNAME = env.str("MQTT_USERNAME", default=None)
MQTT_PASSWORD = env.str("MQTT_PASSWORD", default=None)
MQTT_TLS = env.bool("MQTT_TLS", default=False)

MQTT_QOS = env.int("MQTT_QOS", default=1)
MQTT_KEEPALIVE = env.int("MQTT_KEEPALIVE", default=60)
MQTT_PUBLISH_TIMEOUT = env.float("MQTT_PUBLISH_TIMEOUT", default=5.0)

# Empty means the broker assigns one to each new publisher client / app worker. 
# A fixed id across multiple workers makes
# brokers evict duplicate sessions, so workers would disconnect each other.
MQTT_CLIENT_ID = env.str("MQTT_CLIENT_ID", default="")

