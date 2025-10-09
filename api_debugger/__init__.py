"""
API Debugger - A Python library for debugging API calls with integrations for Django REST Framework and FastAPI.
"""

__version__ = "0.1.0"
__author__ = "API Debugger Team"

from .client import APIClient
from .config import APIDebuggerConfig, configure
from .exceptions import (
    APIDebuggerException,
    ConfigurationError,
    ClientError,
    RetryExhausted,
)

# Framework integrations
try:
    from .django_middleware import APIDebuggerMiddleware as DjangoMiddleware
except ImportError:
    DjangoMiddleware = None

try:
    from .fastapi_middleware import APIDebuggerMiddleware as FastAPIMiddleware
except ImportError:
    FastAPIMiddleware = None

__all__ = [
    "APIClient",
    "APIDebuggerConfig", 
    "configure",
    "APIDebuggerException",
    "ConfigurationError", 
    "ClientError",
    "RetryExhausted",
    "DjangoMiddleware",
    "FastAPIMiddleware",
]