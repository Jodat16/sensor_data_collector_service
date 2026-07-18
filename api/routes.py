from flask import jsonify, Blueprint, request

bp = Blueprint('api', __name__)


@bp.route('/api/sensors/<device_id>/readings', methods=['POST'])
def publish_reading(device_id):
    value = request.form.get('value', default=None, type=str)
    timestamp = request.form.get('timestamp', default=None, type=str)

    reading = {
        "device_id" : device_id,
        "value" : value,
        "timestamp": timestamp
    }

    response = jsonify(reading)
    response.headers['Access-Control-Allow-Origin'] = '*'

    response.status_code = 200
    return response

