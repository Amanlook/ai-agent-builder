"""
Custom exceptions for the API Debugger library.
"""


class APIDebuggerException(Exception):
    """Base exception for all API Debugger errors."""
    pass


class ConfigurationError(APIDebuggerException):
    """Raised when there's an error in configuration."""
    pass


class ClientError(APIDebuggerException):
    """Raised when there's an error in the API client."""
    pass


class RetryExhausted(ClientError):
    """Raised when all retry attempts have been exhausted."""
    
    def __init__(self, attempts: int, last_exception: Exception):
        self.attempts = attempts
        self.last_exception = last_exception
        super().__init__(f"Retry exhausted after {attempts} attempts. Last error: {last_exception}")


class MiddlewareError(APIDebuggerException):
    """Raised when there's an error in middleware processing."""
    pass