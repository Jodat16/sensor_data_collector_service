Requirements for the data collector

* REQ-1 - received messages must be checked for format and plausibilty:
  * value of the reading  must be between -50.00 and +110.00 (˚C)
  * timestamp is a Unix Epoch Timestamp (seconds since 1970-01-01 00:00:00) in UTC timezone
  * timestamp must be in the interval +/- 600 seconds of the local current time (assuming local time is also in the UTC timezone)
* REQ-2 - the received and validated data must be published to a given topic as json payload to an MQTT broker (assuming that the broker is running on localhost, standard MQTT port and requires no authentication)
* REQ-3 - the implementation must follow the 12-factor-app principles


