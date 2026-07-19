# Application factory

import atexit
import logging

from flask import Flask

from . import settings
from .publisher import Publisher
from .routes import bp

def create_app():
    logging.basicConfig(
        level=logging.getLevelName(settings.LOG_LEVEL),
        format='%(asctime)s %(name)s %(levelname)s %(message)s')

    app = Flask(__name__)
    app.config.from_object(settings)

    # One publisher per process. Built here rather than at module level so each
    # worker gets its own client 
    app.publisher = Publisher.from_settings(settings)
    app.publisher.start()
    atexit.register(app.publisher.close)

    app.register_blueprint(bp)

    return app
