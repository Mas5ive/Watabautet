class ImpossibleTaskError(Exception):
    """
    Custom exception raised when a task encounters an impossible state or
    a condition that prevents it from completing successfully, even after retries.
    """
    pass
