# Sensor data collector service

service implemented in Flask that accepts sensor readings and publishes them to an MQTT broker.

## Running locally
* to start the service
  * place .env file at root 
  * change into the root directory
  * set up an environment Linux(e.g. `python -m venv venv`, `. ./venv/bin/activate`, `pip install -r requirements.txt`)
  * set up an environment Windows(e.g. `python -m venv venv`, `source venv/Scripts/activate`, `pip install -r requirements.txt`) 
  * adapt `.env` according to your needs
  * start the service `python run.py`
* use e.g. `curl` to test the service: `curl -X POST localhost:5000/api/sensors/0001/readings -d "value=109&timestamp=1752243577"`
