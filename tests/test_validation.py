# REQ-1 validations unit tests.

import pytest

from api.errors import ErrorCode, ValidationError
from api.validation import (
    TIMESTAMP_TOLERANCE_SECONDS,
    validate_reading,
    validate_timestamp,
    validate_value,
)

NOW = 1752243577

def failing_fields(device_id='0001', value='20.0', timestamp=str(NOW), now=NOW):
    """Run a full validation and return the set of fields that failed."""
    with pytest.raises(ValidationError) as raised:
        validate_reading(device_id=device_id, value=value, timestamp=timestamp, now=now)
    return {error['field'] for error in raised.value.errors}

class TestValue:
    @pytest.mark.parametrize('raw', ['-50.00', '110.00'])
    def test_accepts_value_bounds(self, raw):
        """Test to check that range is inclusive"""
        _, error = validate_value(raw)
        assert error is None

    @pytest.mark.parametrize('raw', ['-50.01', '110.01'])
    def test_rejects_just_outside_the_bounds(self, raw):
        _, error = validate_value(raw)
        assert error is not None

    @pytest.mark.parametrize('raw', ['20', '20.5', '20.50', '-0.01', '1E+1'])
    def test_accepts_up_to_two_decimal_places(self, raw):
        _, error = validate_value(raw)
        assert error is None

    @pytest.mark.parametrize('raw', ['50.004', '110.004', '-50.001', '20.0001', '1.5E-5'])
    def test_rejects_more_than_two_decimal_places(self, raw):
        _, error = validate_value(raw)
        assert error is not None

    @pytest.mark.parametrize('raw', ['NaN', 'Infinity', '-Infinity'])
    def test_rejects_non_finite_numbers(self, raw):
        _, error = validate_value(raw)
        assert error is not None

    @pytest.mark.parametrize('raw', ['abc', '', None])
    def test_rejects_invalid_input(self, raw):
        _, error = validate_value(raw)
        assert error is not None

class TestTimestamp:
    @pytest.mark.parametrize('offset', [-TIMESTAMP_TOLERANCE_SECONDS, 0, TIMESTAMP_TOLERANCE_SECONDS])
    def test_accepts_the_window_boundaries(self, offset):
        _, error = validate_timestamp(str(NOW + offset), now=NOW)
        assert error is None

    @pytest.mark.parametrize(
        'offset', [-TIMESTAMP_TOLERANCE_SECONDS - 1, TIMESTAMP_TOLERANCE_SECONDS + 1]
    )
    def test_rejects_outside_the_window(self, offset):
        _, error = validate_timestamp(str(NOW + offset), now=NOW)
        assert error is not None

    def test_rejects_fractional_seconds(self):
        _, error = validate_timestamp('1752243577.5', now=NOW)
        assert error is not None

    @pytest.mark.parametrize('raw', ['abc', '', None])
    def test_rejects_invalid_input(self, raw):
        _, error = validate_timestamp(raw, now=NOW)
        assert error is not None

class TestDeviceId:
    def test_preserves_leading_zeros(self):
        reading = validate_reading(device_id='0001', value='20.0', timestamp=str(NOW), now=NOW)
        assert reading['device_id'] == '0001'
        assert isinstance(reading['device_id'], str)

    @pytest.mark.parametrize('device_id', ['123', '12345', 'abcd', '00a1', ''])
    def test_rejects_anything_but_four_digits(self, device_id):
        assert 'device_id' in failing_fields(device_id=device_id)

class TestReading:
    def test_returns_typed_fields(self):
        """value must be a JSON number and timestamp a JSON integer"""
        reading = validate_reading(device_id='0001', value='109', timestamp=str(NOW), now=NOW)
        assert reading == {'device_id': '0001', 'value': 109.0, 'timestamp': NOW}
        assert isinstance(reading['value'], float)
        assert isinstance(reading['timestamp'], int)

    @pytest.mark.parametrize(
        'value,timestamp,expected',
        [
            (None, str(NOW), ErrorCode.VALUE_MISSING),
            ('abc', str(NOW), ErrorCode.VALUE_NOT_A_NUMBER),
            ('999', str(NOW), ErrorCode.VALUE_OUT_OF_RANGE),
            ('20.004', str(NOW), ErrorCode.VALUE_TOO_PRECISE),
            ('20.0', None, ErrorCode.TIMESTAMP_MISSING),
            ('20.0', 'abc', ErrorCode.TIMESTAMP_NOT_INTEGER),
            ('20.0', str(NOW + 601), ErrorCode.TIMESTAMP_OUT_OF_WINDOW),
        ],
    )
    def test_each_failure_carries_its_own_code(self, value, timestamp, expected):
        with pytest.raises(ValidationError) as raised:
            validate_reading(device_id='0001', value=value, timestamp=timestamp, now=NOW)

        assert [error['code'] for error in raised.value.errors] == [expected]

    def test_reports_every_error_at_once(self):
        """errors related to all fields must be retunred at once"""
        assert failing_fields(device_id='a/b', value='999', timestamp='abc') == {
            'device_id',
            'value',
            'timestamp',
        }
