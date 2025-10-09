"""
Utility functions for API Debugger.
"""

import json
import time
from typing import Dict, Any, List, Optional
from urllib.parse import urlencode, urlparse, parse_qs


def mask_sensitive_data(data: Any, mask_fields: List[str], mask_char: str = "*") -> Any:
    """
    Recursively mask sensitive fields in data structures.
    
    Args:
        data: The data to mask (dict, list, or primitive)
        mask_fields: List of field names to mask
        mask_char: Character to use for masking
    
    Returns:
        Data with sensitive fields masked
    """
    if isinstance(data, dict):
        masked = {}
        for key, value in data.items():
            if any(field.lower() in key.lower() for field in mask_fields):
                if isinstance(value, str) and len(value) > 0:
                    # Show first 2 chars and mask the rest
                    masked[key] = value[:2] + mask_char * max(8, len(value) - 2)
                else:
                    masked[key] = mask_char * 8
            else:
                masked[key] = mask_sensitive_data(value, mask_fields, mask_char)
        return masked
    elif isinstance(data, list):
        return [mask_sensitive_data(item, mask_fields, mask_char) for item in data]
    else:
        return data


def generate_curl_command(
    method: str,
    url: str,
    headers: Optional[Dict[str, str]] = None,
    data: Optional[Any] = None,
    params: Optional[Dict[str, Any]] = None,
    mask_fields: Optional[List[str]] = None
) -> str:
    """
    Generate a cURL command from request parameters.
    
    Args:
        method: HTTP method
        url: Request URL
        headers: Request headers
        data: Request body data
        params: URL parameters
        mask_fields: Fields to mask in the output
    
    Returns:
        cURL command string
    """
    if mask_fields is None:
        mask_fields = ["password", "Authorization", "token", "secret"]
    
    curl_parts = ["curl", "-X", method.upper()]
    
    # Add URL with parameters
    if params:
        separator = "&" if "?" in url else "?"
        url += separator + urlencode(params)
    
    curl_parts.extend([f'"{url}"'])
    
    # Add headers
    if headers:
        masked_headers = mask_sensitive_data(headers, mask_fields)
        for key, value in masked_headers.items():
            curl_parts.extend(["-H", f'"{key}: {value}"'])
    
    # Add data
    if data is not None:
        if isinstance(data, (dict, list)):
            masked_data = mask_sensitive_data(data, mask_fields)
            json_data = json.dumps(masked_data, indent=None, separators=(',', ':'))
            curl_parts.extend(["-d", f"'{json_data}'"])
        else:
            curl_parts.extend(["-d", f"'{data}'"])
    
    return " ".join(curl_parts)


def truncate_body(body: str, max_length: int = 10000) -> str:
    """
    Truncate request/response body if it exceeds max length.
    
    Args:
        body: The body content
        max_length: Maximum allowed length
    
    Returns:
        Truncated body with indicator if truncated
    """
    if len(body) <= max_length:
        return body
    
    truncated = body[:max_length]
    return truncated + f"\n... [TRUNCATED - {len(body) - max_length} more characters]"


def format_json(data: Any, indent: int = 2) -> str:
    """
    Format data as pretty JSON string.
    
    Args:
        data: Data to format
        indent: Indentation level
    
    Returns:
        Formatted JSON string
    """
    try:
        if isinstance(data, str):
            # Try to parse if it's a JSON string
            data = json.loads(data)
        return json.dumps(data, indent=indent, ensure_ascii=False)
    except (json.JSONDecodeError, TypeError):
        return str(data)


def sanitize_url(url: str, mask_fields: Optional[List[str]] = None) -> str:
    """
    Sanitize URL by masking sensitive query parameters.
    
    Args:
        url: The URL to sanitize
        mask_fields: Fields to mask in query parameters
    
    Returns:
        Sanitized URL
    """
    if mask_fields is None:
        mask_fields = ["password", "Authorization", "token", "secret", "key"]
    
    parsed = urlparse(url)
    if not parsed.query:
        return url
    
    query_params = parse_qs(parsed.query, keep_blank_values=True)
    
    # Mask sensitive parameters
    for param, values in query_params.items():
        if any(field.lower() in param.lower() for field in mask_fields):
            query_params[param] = ["***MASKED***"] * len(values)
    
    # Rebuild query string
    sanitized_query = urlencode(query_params, doseq=True)
    
    # Reconstruct URL
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path}?{sanitized_query}"


def get_content_type(headers: Dict[str, str]) -> str:
    """
    Get content type from headers.
    
    Args:
        headers: HTTP headers
    
    Returns:
        Content type or empty string if not found
    """
    for key, value in headers.items():
        if key.lower() == 'content-type':
            return value.split(';')[0].strip()
    return ""


def is_json_content(content_type: str) -> bool:
    """
    Check if content type indicates JSON.
    
    Args:
        content_type: Content type string
    
    Returns:
        True if content type is JSON-related
    """
    json_types = [
        'application/json',
        'application/vnd.api+json',
        'text/json'
    ]
    return any(json_type in content_type.lower() for json_type in json_types)


def format_duration(duration: float) -> str:
    """
    Format duration in a human-readable way.
    
    Args:
        duration: Duration in seconds
    
    Returns:
        Formatted duration string
    """
    if duration < 0.001:
        return f"{duration * 1000000:.0f}μs"
    elif duration < 1:
        return f"{duration * 1000:.1f}ms"
    else:
        return f"{duration:.2f}s"


class Timer:
    """Context manager for timing operations."""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.duration = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time
    
    def get_duration(self) -> float:
        """Get the measured duration."""
        if self.duration is not None:
            return self.duration
        elif self.start_time is not None:
            return time.time() - self.start_time
        else:
            return 0.0