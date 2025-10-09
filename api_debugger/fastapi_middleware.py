"""
FastAPI middleware for API debugging.
"""

from typing import Dict, Any, Callable

try:
    from fastapi import Request, Response
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.responses import Response as StarletteResponse
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    # Create dummy classes for when FastAPI is not available
    class BaseHTTPMiddleware:
        pass
    
    class Request:
        pass
    
    class Response:
        pass
    
    class StarletteResponse:
        pass

from .config import get_config, APIDebuggerConfig
from .logger import get_logger
from .utils import (
    generate_curl_command,
    mask_sensitive_data,
    Timer
)
from .exceptions import MiddlewareError


class APIDebuggerMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for debugging API requests and responses.
    
    Add this middleware to your FastAPI app to enable API debugging:
    
    from api_debugger import FastAPIMiddleware
    
    app = FastAPI()
    app.add_middleware(FastAPIMiddleware)
    
    Configuration can be done via environment variables or by passing a config:
    
    app.add_middleware(FastAPIMiddleware, config={
        "enabled": True,
        "mask_fields": ["password", "Authorization"],
        "log_to": "console",
        "pretty": True,
        "curl": True
    })
    """
    
    def __init__(self, app, config: Dict[str, Any] = None):
        """
        Initialize the middleware.
        
        Args:
            app: FastAPI app instance
            config: Configuration dictionary
        """
        if not FASTAPI_AVAILABLE:
            raise MiddlewareError("FastAPI is required for FastAPI middleware")
        
        super().__init__(app)
        
        # Load configuration
        if config:
            self.config = APIDebuggerConfig.from_dict(config)
        else:
            self.config = get_config()
        
        self.logger = get_logger("api_debugger.fastapi")
    
    async def dispatch(self, request: Request, call_next: Callable) -> StarletteResponse:
        """Process the request and response."""
        if not self.config.enabled:
            return await call_next(request)
        
        # Start timing
        timer = Timer()
        timer.__enter__()
        
        try:
            # Capture request data
            request_data = await self._capture_request(request)
            
            # Process the request
            response = await call_next(request)
            
            # Capture response data
            response_data = await self._capture_response(response)
            
            # Stop timing
            timer.__exit__(None, None, None)
            
            # Log the request/response
            self._log_request_response(request_data, response_data, timer.get_duration())
            
            return response
            
        except Exception as e:
            timer.__exit__(None, None, None)
            if self.config.enabled:
                self.logger.log_error(f"Middleware error: {e}", exc_info=e)
            raise
    
    async def _capture_request(self, request: Request) -> Dict[str, Any]:
        """Capture request data for logging."""
        try:
            # Get request body
            body = None
            try:
                body_bytes = await request.body()
                if body_bytes:
                    body = body_bytes.decode('utf-8')
            except Exception:
                body = "<Could not decode body>"
            
            # Get headers
            headers = dict(request.headers)
            
            # Get query parameters
            params = dict(request.query_params)
            
            # Get client IP
            client_ip = "unknown"
            if hasattr(request, 'client') and request.client:
                client_ip = request.client.host
            
            return {
                'method': request.method,
                'url': str(request.url),
                'path': request.url.path,
                'headers': headers,
                'body': body,
                'params': params,
                'client_ip': client_ip
            }
            
        except Exception as e:
            self.logger.log_error(f"Error capturing request: {e}")
            return {
                'method': getattr(request, 'method', 'unknown'),
                'url': 'unknown',
                'path': 'unknown',
                'headers': {},
                'body': None,
                'params': {},
                'client_ip': 'unknown'
            }
    
    async def _capture_response(self, response: StarletteResponse) -> Dict[str, Any]:
        """Capture response data for logging."""
        try:
            # Get response body
            content = None
            if hasattr(response, 'body'):
                try:
                    if isinstance(response.body, bytes):
                        content = response.body.decode('utf-8')
                    else:
                        content = str(response.body)
                except UnicodeDecodeError:
                    content = f"<Binary data: {len(response.body)} bytes>"
            
            # Get response headers
            headers = dict(response.headers) if hasattr(response, 'headers') else {}
            
            return {
                'status_code': getattr(response, 'status_code', 0),
                'headers': headers,
                'content': content
            }
            
        except Exception as e:
            self.logger.log_error(f"Error capturing response: {e}")
            return {
                'status_code': getattr(response, 'status_code', 0),
                'headers': {},
                'content': None
            }
    
    def _log_request_response(
        self,
        request_data: Dict[str, Any],
        response_data: Dict[str, Any],
        duration: float
    ):
        """Log the request and response."""
        try:
            # Generate cURL command if enabled
            curl_command = None
            if self.config.curl:
                curl_command = generate_curl_command(
                    method=request_data['method'],
                    url=request_data['url'],
                    headers=request_data['headers'],
                    data=request_data['body'],
                    params=request_data['params'],
                    mask_fields=self.config.mask_fields
                )
            
            # Log request
            self.logger.log_request(
                method=request_data['method'],
                url=request_data['url'],
                headers=mask_sensitive_data(request_data['headers'], self.config.mask_fields),
                body=request_data['body'],
                curl_command=curl_command
            )
            
            # Log response
            self.logger.log_response(
                status_code=response_data['status_code'],
                headers=response_data['headers'],
                body=response_data['content'],
                duration=duration
            )
            
        except Exception as e:
            self.logger.log_error(f"Error logging request/response: {e}")


class APIDebuggerHTTPException:
    """Custom exception handler for API debugging."""
    
    def __init__(self, config: APIDebuggerConfig = None):
        self.config = config or get_config()
        self.logger = get_logger("api_debugger.fastapi.exceptions")
    
    async def __call__(self, request: Request, exc: Exception):
        """Handle HTTP exceptions with debugging."""
        if self.config.enabled:
            self.logger.log_error(
                f"HTTP Exception on {request.method} {request.url}: {exc}",
                exc_info=exc
            )
        
        # Re-raise the exception to let FastAPI handle it normally
        raise exc


def create_debug_app_factory(config: Dict[str, Any] = None):
    """
    Factory function to create a FastAPI app with debugging enabled.
    
    Args:
        config: Configuration dictionary
    
    Returns:
        Function that creates FastAPI app with debugging
    """
    def create_app():
        if not FASTAPI_AVAILABLE:
            raise MiddlewareError("FastAPI is required")
        
        from fastapi import FastAPI
        
        app = FastAPI()
        app.add_middleware(APIDebuggerMiddleware, config=config)
        
        return app
    
    return create_app


# Utility function for adding debugging to existing FastAPI apps
def add_api_debugging(app, config: Dict[str, Any] = None):
    """
    Add API debugging to an existing FastAPI app.
    
    Args:
        app: FastAPI app instance
        config: Configuration dictionary
    """
    if not FASTAPI_AVAILABLE:
        raise MiddlewareError("FastAPI is required")
    
    app.add_middleware(APIDebuggerMiddleware, config=config)
    
    # Optionally add exception handler
    debug_config = APIDebuggerConfig.from_dict(config) if config else get_config()
    if debug_config.enabled:
        exception_handler = APIDebuggerHTTPException(debug_config)
        app.add_exception_handler(Exception, exception_handler)