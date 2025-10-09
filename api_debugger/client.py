"""
API Client with debugging capabilities.
"""

import time
from typing import Dict, Any, Optional, Union, Callable
import json

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

from .config import get_config, APIDebuggerConfig
from .logger import get_logger
from .utils import (
    generate_curl_command, 
    mask_sensitive_data, 
    sanitize_url, 
    Timer,
    get_content_type,
    is_json_content
)
from .exceptions import ClientError, RetryExhausted, ConfigurationError


class APIClient:
    """
    API client with debugging capabilities.
    
    Supports both requests and httpx backends with comprehensive logging,
    retry mechanisms, and cURL export functionality.
    """
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        debug: bool = True,
        config: Optional[APIDebuggerConfig] = None,
        backend: str = "auto"  # "requests", "httpx", or "auto"
    ):
        """
        Initialize the API client.
        
        Args:
            base_url: Base URL for all requests
            debug: Enable debug logging
            config: Custom configuration (uses global config if None)
            backend: HTTP backend to use
        """
        self.base_url = base_url.rstrip('/') if base_url else None
        self.debug = debug
        self.config = config or get_config()
        self.logger = get_logger()
        
        # Set up HTTP backend
        self._setup_backend(backend)
        
        # Default headers and session configuration
        self.default_headers = {}
        self.default_timeout = self.config.timeout
        
    def _setup_backend(self, backend: str):
        """Set up the HTTP backend."""
        if backend == "auto":
            if HTTPX_AVAILABLE:
                self.backend = "httpx"
                self._client = httpx.Client()
            elif REQUESTS_AVAILABLE:
                self.backend = "requests"
                self._session = requests.Session()
            else:
                raise ConfigurationError("Neither requests nor httpx is available")
        elif backend == "requests":
            if not REQUESTS_AVAILABLE:
                raise ConfigurationError("requests library is not available")
            self.backend = "requests"
            self._session = requests.Session()
        elif backend == "httpx":
            if not HTTPX_AVAILABLE:
                raise ConfigurationError("httpx library is not available")
            self.backend = "httpx"
            self._client = httpx.Client()
        else:
            raise ConfigurationError(f"Unknown backend: {backend}")
    
    def set_default_headers(self, headers: Dict[str, str]):
        """Set default headers for all requests."""
        self.default_headers.update(headers)
        
        if self.backend == "requests":
            self._session.headers.update(headers)
        elif self.backend == "httpx":
            self._client.headers.update(headers)
    
    def set_auth(self, auth: Any):
        """Set authentication for all requests."""
        if self.backend == "requests":
            self._session.auth = auth
        elif self.backend == "httpx":
            self._client.auth = auth
    
    def _build_url(self, endpoint: str) -> str:
        """Build full URL from endpoint."""
        if endpoint.startswith('http'):
            return endpoint
        
        if self.base_url:
            return f"{self.base_url}/{endpoint.lstrip('/')}"
        
        return endpoint
    
    def _prepare_request_data(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        json_data: Optional[Any] = None,
        data: Optional[Any] = None,
        params: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Prepare request data."""
        # Merge headers
        final_headers = {**self.default_headers}
        if headers:
            final_headers.update(headers)
        
        # Prepare body
        body_content = None
        if json_data is not None:
            final_headers['Content-Type'] = 'application/json'
            body_content = json.dumps(json_data)
        elif data is not None:
            body_content = data
        
        return {
            'method': method.upper(),
            'url': self._build_url(url),
            'headers': final_headers,
            'params': params,
            'body': body_content,
            'json_data': json_data,
            'data': data,
            'kwargs': kwargs
        }
    
    def _make_request_with_backend(self, request_data: Dict[str, Any]):
        """Make request using the configured backend."""
        if self.backend == "requests":
            return self._make_requests_request(request_data)
        elif self.backend == "httpx":
            return self._make_httpx_request(request_data)
    
    def _make_requests_request(self, request_data: Dict[str, Any]):
        """Make request using requests library."""
        kwargs = {
            'timeout': self.default_timeout,
            **request_data['kwargs']
        }
        
        if request_data['json_data'] is not None:
            kwargs['json'] = request_data['json_data']
        elif request_data['data'] is not None:
            kwargs['data'] = request_data['data']
        
        if request_data['params']:
            kwargs['params'] = request_data['params']
        
        return self._session.request(
            method=request_data['method'],
            url=request_data['url'],
            headers=request_data['headers'],
            **kwargs
        )
    
    def _make_httpx_request(self, request_data: Dict[str, Any]):
        """Make request using httpx library."""
        kwargs = {
            'timeout': self.default_timeout,
            **request_data['kwargs']
        }
        
        if request_data['json_data'] is not None:
            kwargs['json'] = request_data['json_data']
        elif request_data['data'] is not None:
            kwargs['content'] = request_data['data']
        
        if request_data['params']:
            kwargs['params'] = request_data['params']
        
        return self._client.request(
            method=request_data['method'],
            url=request_data['url'],
            headers=request_data['headers'],
            **kwargs
        )
    
    def _extract_response_data(self, response) -> Dict[str, Any]:
        """Extract response data from backend response."""
        if self.backend == "requests":
            return {
                'status_code': response.status_code,
                'headers': dict(response.headers),
                'content': response.text,
                'url': str(response.url)
            }
        elif self.backend == "httpx":
            return {
                'status_code': response.status_code,
                'headers': dict(response.headers),
                'content': response.text,
                'url': str(response.url)
            }
    
    def _log_request_response(
        self,
        request_data: Dict[str, Any],
        response_data: Dict[str, Any],
        duration: float,
        curl_command: Optional[str] = None
    ):
        """Log request and response if debugging is enabled."""
        if not (self.debug and self.config.enabled):
            return
        
        # Log request
        self.logger.log_request(
            method=request_data['method'],
            url=sanitize_url(request_data['url'], self.config.mask_fields),
            headers=request_data['headers'],
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
    
    def request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        json: Optional[Any] = None,
        data: Optional[Any] = None,
        params: Optional[Dict[str, Any]] = None,
        retry_on_failure: Optional[bool] = None,
        **kwargs
    ):
        """
        Make an HTTP request with debugging and retry capabilities.
        
        Args:
            method: HTTP method
            url: Request URL or endpoint
            headers: Request headers
            json: JSON data to send
            data: Raw data to send
            params: URL parameters
            retry_on_failure: Whether to retry on failure (uses config default if None)
            **kwargs: Additional arguments passed to the backend
        
        Returns:
            Response object from the backend
        
        Raises:
            RetryExhausted: If all retry attempts fail
            ClientError: For other client-related errors
        """
        if retry_on_failure is None:
            retry_on_failure = self.config.max_retries > 0
        
        request_data = self._prepare_request_data(
            method, url, headers, json, data, params, **kwargs
        )
        
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
        
        last_exception = None
        
        for attempt in range(self.config.max_retries + 1):
            try:
                with Timer() as timer:
                    response = self._make_request_with_backend(request_data)
                
                response_data = self._extract_response_data(response)
                
                # Log request and response
                self._log_request_response(
                    request_data, response_data, timer.get_duration(), curl_command
                )
                
                return response
                
            except Exception as e:
                last_exception = e
                
                if not retry_on_failure or attempt == self.config.max_retries:
                    if self.debug and self.config.enabled:
                        self.logger.log_error(
                            f"Request failed after {attempt + 1} attempts",
                            exc_info=e
                        )
                    break
                
                if self.debug and self.config.enabled:
                    self.logger.log_warning(
                        f"Request failed (attempt {attempt + 1}/{self.config.max_retries + 1}), retrying..."
                    )
                
                # Wait before retry
                if self.config.retry_delay > 0:
                    time.sleep(self.config.retry_delay)
        
        # If we get here, all retries failed
        if retry_on_failure and self.config.max_retries > 0:
            raise RetryExhausted(self.config.max_retries + 1, last_exception)
        else:
            raise ClientError(f"Request failed: {last_exception}") from last_exception
    
    # Convenience methods for different HTTP verbs
    def get(self, url: str, **kwargs):
        """Make a GET request."""
        return self.request('GET', url, **kwargs)
    
    def post(self, url: str, **kwargs):
        """Make a POST request."""
        return self.request('POST', url, **kwargs)
    
    def put(self, url: str, **kwargs):
        """Make a PUT request."""
        return self.request('PUT', url, **kwargs)
    
    def patch(self, url: str, **kwargs):
        """Make a PATCH request."""
        return self.request('PATCH', url, **kwargs)
    
    def delete(self, url: str, **kwargs):
        """Make a DELETE request."""
        return self.request('DELETE', url, **kwargs)
    
    def head(self, url: str, **kwargs):
        """Make a HEAD request."""
        return self.request('HEAD', url, **kwargs)
    
    def options(self, url: str, **kwargs):
        """Make an OPTIONS request."""
        return self.request('OPTIONS', url, **kwargs)
    
    def close(self):
        """Close the client and clean up resources."""
        if hasattr(self, '_session'):
            self._session.close()
        elif hasattr(self, '_client'):
            self._client.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()