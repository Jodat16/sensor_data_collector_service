from  __main__ import app
import settings
from flask import json, request


@app.route('/api/sensors/<device_id>/readings', methods=['POST'])
def get_configuration(device_id):
    response = app.response_class(mimetype='application/json')
    response.headers['Access-Control-Allow-Origin'] = '*'

    value = request.form.get('value', default=None, type=str)
    timestamp = request.form.get('timestamp', default=None, type=str)

    response.status = 200

    reading = {
        "device_id" : device_id,
        "value" : value,
        "timestamp": timestamp
    }
    response.response = json.dumps(reading)
    
    return response

