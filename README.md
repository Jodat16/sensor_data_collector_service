# start the service

* the service is implemented in Python using Flask
* to start the service
  * change into the `api` directory
  * set up an environment (e.g. `python -m venv venv`, `. ./venv/bin/activate`, `pip install -r requirements.txt`)
  * adapt `.env` according to your needs
  * start the service `python service.py`
* use e.g. `curl` to test the service: `curl -X POST localhost:5000/api/sensors/0001/readings -d "value=109&timestamp=1752243577"`
