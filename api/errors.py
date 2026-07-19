# Domain errors


class ErrorCode:
    """Machine-readable error codes returned to the sensor."""

    VALUE_MISSING = '0001'
    VALUE_NOT_A_NUMBER = '0002'
    VALUE_OUT_OF_RANGE = '0003'
    VALUE_TOO_PRECISE = '0004'

    TIMESTAMP_MISSING = '0005'
    TIMESTAMP_NOT_INTEGER = '0006'
    TIMESTAMP_OUT_OF_WINDOW = '0007'

    DEVICE_ID_INVALID = '0008'

    BROKER_UNAVAILABLE = '0100'


class ValidationError(Exception):
    """Raised when a reading validation fails."""

    def __init__(self, errors):
        self.errors = errors
        super().__init__(f'{len(errors)} validation error(s)')

class PublishError(Exception):
    """Raised when the broker did not confirm a reading.

    Covers an unreachable broker, a rejected publish and a confirmation
    timeout. Raise 503 - service unavailable.
    """