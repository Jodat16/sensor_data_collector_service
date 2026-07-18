# Application factory

import logging

from flask import Flask

from . import settings
from .routes import bp


def create_app():
    logging.basicConfig(
        level=logging.getLevelName(settings.LOG_LEVEL),
        format='%(asctime)s %(name)s %(levelname)s %(message)s')

    app = Flask(__name__)
    app.config.from_object(settings)
    app.register_blueprint(bp)

    return app
