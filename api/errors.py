# Domain errors

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