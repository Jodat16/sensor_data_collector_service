from flask import Flask
import settings
import logging


logging.basicConfig(
    level=logging.getLevelName(settings.LOG_LEVEL),
    format='%(asctime)s %(name)s %(levelname)s %(message)s')

app = Flask(__name__)
app.config.from_object("settings")

import routes

if __name__ == '__main__':
        app.run(host=settings.HOST ,debug=settings.DEBUG, port=settings.PORT)
