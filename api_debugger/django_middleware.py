"""
Django REST Framework middleware for API debugging.
"""

from typing import Dict, Any

try:
    from django.conf import settings
    from django.http import HttpRequest, HttpResponse
    from django.utils.deprecation import MiddlewareMixin
    DJANGO_AVAILABLE = True
except ImportError:
    DJANGO_AVAILABLE = False
    # Create dummy classes for when Django is not available
    class MiddlewareMixin:
        pass
    
    class HttpRequest:
        pass
    
    class HttpResponse:
        pass

from .config import get_config, APIDebuggerConfig
from .logger import get_logger
from .utils import (
    generate_curl_command,
    mask_sensitive_data,
    Timer
)
from .exceptions import MiddlewareError


class APIDebuggerMiddleware(MiddlewareMixin):
    """
    Django middleware for debugging API requests and responses.
    
    Add this middleware to your Django settings to enable API debugging:
    
    MIDDLEWARE = [
        ...
        'api_debugger.django_middleware.APIDebuggerMiddleware',
        ...
    ]
    
    Configuration can be done via Django settings:
    
    API_DEBUGGER = {
        "enabled": True,
        "mask_fields": ["password", "Authorization"],
        "log_to": "console",
        "pretty": True,
        "curl": True
    }
    """
    
    def __init__(self, get_response=None):
        """Initialize the middleware."""
        super().__init__(get_response)
        self.get_response = get_response
        
        # Load configuration from Django settings or use defaults
        self.config = self._load_config()
        self.logger = get_logger("api_debugger.django")
        
        if not DJANGO_AVAILABLE:
            raise MiddlewareError("Django is required for Django middleware")
    
    def _load_config(self) -> APIDebuggerConfig:
        """Load configuration from Django settings."""
        if DJANGO_AVAILABLE and hasattr(settings, 'API_DEBUGGER'):
            django_config = getattr(settings, 'API_DEBUGGER', {})
            return APIDebuggerConfig.from_dict(django_config)
        else:
            return get_config()
    
    def __call__(self, request: HttpRequest) -> HttpResponse:
        """Process the request and response."""
        if not self.config.enabled:
            return self.get_response(request)
        
        # Start timing
        timer = Timer()
        timer.__enter__()
        
        try:
            # Capture request data
            request_data = self._capture_request(request)
            
            # Process the request
            response = self.get_response(request)
            
            # Capture response data
            response_data = self._capture_response(response)
            
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
    
    def _capture_request(self, request: HttpRequest) -> Dict[str, Any]:
        """Capture request data for logging."""
        try:
            # Get request body
            body = None
            if hasattr(request, 'body'):
                body_bytes = request.body
                if body_bytes:
                    try:
                        body = body_bytes.decode('utf-8')
                    except UnicodeDecodeError:
                        body = f"<Binary data: {len(body_bytes)} bytes>"
            
            # Get headers
            headers = {}
            if hasattr(request, 'META'):
                for key, value in request.META.items():
                    if key.startswith('HTTP_'):
                        header_name = key[5:].replace('_', '-').title()
                        headers[header_name] = str(value)
                    elif key in ['CONTENT_TYPE', 'CONTENT_LENGTH']:
                        headers[key.replace('_', '-').title()] = str(value)
            
            # Get query parameters
            params = dict(request.GET) if hasattr(request, 'GET') else {}
            
            return {
                'method': request.method,
                'url': request.get_full_path() if hasattr(request, 'get_full_path') else str(request),
                'headers': headers,
                'body': body,
                'params': params,
                'remote_addr': getattr(request, 'META', {}).get('REMOTE_ADDR', 'unknown')
            }
            
        except Exception as e:
            self.logger.log_error(f"Error capturing request: {e}")
            return {
                'method': getattr(request, 'method', 'unknown'),
                'url': 'unknown',
                'headers': {},
                'body': None,
                'params': {},
                'remote_addr': 'unknown'
            }
    
    def _capture_response(self, response: HttpResponse) -> Dict[str, Any]:
        """Capture response data for logging."""
        try:
            # Get response content
            content = None
            if hasattr(response, 'content'):
                try:
                    content = response.content.decode('utf-8')
                except UnicodeDecodeError:
                    content = f"<Binary data: {len(response.content)} bytes>"
            
            # Get response headers
            headers = {}
            if hasattr(response, 'headers'):
                headers = dict(response.headers)
            elif hasattr(response, '_headers'):
                headers = {k: v[1] for k, v in response._headers.items()}
            
            return {
                'status_code': getattr(response, 'status_code', 0),
                'headers': headers,
                'content': content,
                'reason_phrase': getattr(response, 'reason_phrase', '')
            }
            
        except Exception as e:
            self.logger.log_error(f"Error capturing response: {e}")
            return {
                'status_code': getattr(response, 'status_code', 0),
                'headers': {},
                'content': None,
                'reason_phrase': ''
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
                # Build full URL for cURL (we only have the path in Django)
                scheme = 'https'  # Default to HTTPS, could be made configurable
                host = 'example.com'  # This should ideally come from request.get_host()
                full_url = f"{scheme}://{host}{request_data['url']}"
                
                curl_command = generate_curl_command(
                    method=request_data['method'],
                    url=full_url,
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


# Alternative function-based middleware for older Django versions
def api_debugger_middleware(get_response):
    """
    Function-based middleware for API debugging.
    
    This is an alternative to the class-based middleware for Django versions
    that prefer function-based middleware.
    """
    config = get_config()
    logger = get_logger("api_debugger.django")
    
    def middleware(request):
        if not config.enabled:
            return get_response(request)
        
        timer = Timer()
        timer.__enter__()
        
        try:
            # Capture request
            request_data = _capture_request_simple(request)
            
            # Process request
            response = get_response(request)
            
            # Capture response
            response_data = _capture_response_simple(response)
            
            # Stop timing
            timer.__exit__(None, None, None)
            
            # Log
            _log_simple(logger, config, request_data, response_data, timer.get_duration())
            
            return response
            
        except Exception as e:
            timer.__exit__(None, None, None)
            logger.log_error(f"Middleware error: {e}", exc_info=e)
            raise
    
    return middleware


def _capture_request_simple(request) -> Dict[str, Any]:
    """Simple request capture for function-based middleware."""
    return {
        'method': getattr(request, 'method', 'unknown'),
        'url': request.get_full_path() if hasattr(request, 'get_full_path') else 'unknown',
        'body': getattr(request, 'body', b'').decode('utf-8', errors='ignore') if hasattr(request, 'body') else None
    }


def _capture_response_simple(response) -> Dict[str, Any]:
    """Simple response capture for function-based middleware."""
    return {
        'status_code': getattr(response, 'status_code', 0),
        'content': getattr(response, 'content', b'').decode('utf-8', errors='ignore') if hasattr(response, 'content') else None
    }


def _log_simple(logger, config, request_data, response_data, duration):
    """Simple logging for function-based middleware."""
    logger.log_info(
        f"[Django] {request_data['method']} {request_data['url']} -> "
        f"{response_data['status_code']} ({duration:.3f}s)"
    )