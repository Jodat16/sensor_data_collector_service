# Sensor data collector service

service implemented in Flask that accepts sensor readings and publishes them to an MQTT broker.

## Running service locally
* to start the service
  * place .env file at root 
  * change into the root directory
  * set up an environment Linux(e.g. `python -m venv venv`, `. ./venv/bin/activate`, `pip install -r requirements.txt`)
  * set up an environment Windows(e.g. `python -m venv venv`, `source venv/Scripts/activate`, `pip install -r requirements.txt`) 
  * adapt `.env` according to your needs
  * start the service `python run.py`

* to run the broker as a docker container
  * `docker pull eclipse-mosquitto:2`
  * Linux/macOS `docker run -d --name mosquitto -p 1883:1883 -v "$(pwd)/mosquitto/mosquitto.conf:/mosquitto/config/mosquitto.conf" eclipse-mosquitto:2`
  * Windows (cmd) `docker run -d --name mosquitto -p 1883:1883 -v "%cd%/mosquitto/mosquitto.conf:/mosquitto/config/mosquitto.conf" eclipse-mosquitto:2`
  * check it started `docker logs mosquitto`
  * subscribe to the topic to watch incoming readings (leave running in its own terminal)
  `docker exec -it mosquitto mosquitto_sub -t "service/secom/data01" -v`

* use e.g. `curl` to test the service: `curl -X POST localhost:5000/api/sensors/0001/readings -d "value=109&timestamp=1752243577"`

### Responses
| Situation | Status |
| --- | --- |
| reading validated and confirmed by the broker | `202 Accepted` |
| reading failed validation | `400 Bad Request`, with the offending fields |
| broker unreachable or did not confirm in time | `503 Service Unavailable`, with `Retry-After` |

A published reading appears in the subscriber terminal as
`service/secom/data01 {"device_id":"0001","value":109.0,"timestamp":1752243577}`.

## Running tests
* change into the root directory
* activate python virtual environment with all dependencies
* `pip install -r requirements-dev.txt`
* run `python -m pytest`