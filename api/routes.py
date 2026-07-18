from flask import jsonify, Blueprint, request

from . import validation
from .errors import ValidationError

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
        response = jsonify(errors=error.errors)
        response.status_code = 400
        return response

    response = jsonify(reading)
    response.status_code = 200
    return response
