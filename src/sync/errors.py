def invariant(condition: bool, message: str | None):
    """Assert that a condition holds true, otherwise raise an AssertionError with the provided message."""
    if not condition:
        raise AssertionError(message or str(condition))


type ErrorMessage = str
"""A human-readable error message returned in Result error cases."""
