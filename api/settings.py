from environs import Env

env = Env()
env.read_env()

DEBUG = env.bool("FLASK_DEBUG", default=False)
SECRET_KEY = env.str("FLASK_SECRET_KEY")

LOG_LEVEL = env.str("LOG_LEVEL", default="WARNING")

HOST = env.str("FLASK_HOST", default="127.0.0.1")
PORT = env.int("FLASK_PORT", default=5000)

BROKER_TOPIC = env.str("BROKER_TOPIC", default="service/secom/data01")

