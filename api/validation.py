# REQ-1 -format and plausibility validation

import re
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation

from .errors import ValidationError

VALUE_MIN = Decimal('-50.00')
VALUE_MAX = Decimal('110.00')

VALUE_MAX_DECIMAL_PLACES = 2

TIMESTAMP_TOLERANCE_SECONDS = 600

# device_id is assumed to be always a 4 digit number
DEVICE_ID_PATTERN = re.compile(r'^[0-9]{4}$')


def utc_now():
    """Current UTC time as Unix epoch seconds."""
    return int(datetime.now(timezone.utc).timestamp())


def validate_device_id(device_id):
    if not device_id or not DEVICE_ID_PATTERN.match(device_id):
        return 'must be exactly 4 digits'
    return None


def validate_value(raw):
    """Vlidate temperature reading: at most 2 decimal places, bounds inclusive."""
    if raw is None or raw.strip() == '':
        return None, 'is required'

    try:
        value = Decimal(raw.strip())
    except InvalidOperation:
        return None, 'must be a number'

    if not value.is_finite():
        return None, 'must be a finite number'

    if -value.as_tuple().exponent > VALUE_MAX_DECIMAL_PLACES:
        return None, f'must have at most {VALUE_MAX_DECIMAL_PLACES} decimal places'

    if not VALUE_MIN <= value <= VALUE_MAX:
        return None, f'must be between {VALUE_MIN} and {VALUE_MAX} inclusive'

    return value, None


def validate_timestamp(raw, now):
    """Validate UTC timestamp, must be within +/- TIMESTAMP_TOLERANCE_SECONDS of 'now'."""
    if raw is None or raw.strip() == '':
        return None, 'is required'

    try:
        timestamp = int(raw.strip())
    except ValueError:
        # Also rejects fractional input such as '1752243577.5'
        return None, 'must be an integer number of seconds since the Unix epoch'

    if abs(now - timestamp) > TIMESTAMP_TOLERANCE_SECONDS:
        return None, f'must be within {TIMESTAMP_TOLERANCE_SECONDS} seconds of the current time'

    return timestamp, None


def validate_reading(device_id, value, timestamp, now):
    """Validate complete reading, raising ValidationError with every problem found.

    Returns the reading with typed fields: 
    device_id - 4 digit number
    value - float
    timestamp - int
    """
    errors = []

    device_id_error = validate_device_id(device_id)
    if device_id_error:
        errors.append({'field': 'device_id', 'reason': device_id_error})

    parsed_value, value_error = validate_value(value)
    if value_error:
        errors.append({'field': 'value', 'reason': value_error})

    parsed_timestamp, timestamp_error = validate_timestamp(timestamp, now)
    if timestamp_error:
        errors.append({'field': 'timestamp', 'reason': timestamp_error})

    if errors:
        raise ValidationError(errors)

    return {
        'device_id': device_id,
        'value': float(parsed_value),
        'timestamp': parsed_timestamp,
    }