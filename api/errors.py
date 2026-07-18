# Domain errors

class ValidationError(Exception):
    """Raised when a reading validation fails."""

    def __init__(self, errors):
        self.errors = errors
        super().__init__(f'{len(errors)} validation error(s)')