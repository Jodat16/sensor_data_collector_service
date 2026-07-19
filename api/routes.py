import logging

from flask import jsonify, Blueprint, current_app, request

from . import validation
from .errors import PublishError, ValidationError

logger = logging.getLogger(__name__)

bp = Blueprint('api', __name__)


@bp.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response


@bp.route('/api/sensors/<device_id>/readings', methods=['POST'])
def publish_reading(device_id):
    value = request.form.get('value', default=None, type=str)
    timestamp = request.form.get('timestamp', default=None, type=str)

    try:
        reading = validation.validate_reading(
            device_id=device_id,
            value=value,
            timestamp=timestamp,
            now=validation.utc_now(),
        )
    except ValidationError as error:
        logger.info(
            'reading rejected device_id=%s reasons=%s',
            device_id,
            '; '.join(f"{e['field']} {e['reason']}" for e in error.errors))
        response = jsonify(errors=error.errors)
        response.status_code = 400
        return response

    try:
        current_app.publisher.publish(reading)
    except PublishError as error:
        # broker unavailable
        response = jsonify(error=str(error))
        response.status_code = 503
        response.headers['Retry-After'] = '5'
        return response

    #  the reading has been accepted and forwarded to the broker
    logger.debug('reading published device_id=%s', reading['device_id'])

    response = jsonify(reading)
    response.status_code = 202
    return response
