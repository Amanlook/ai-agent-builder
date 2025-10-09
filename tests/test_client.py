"""
Comprehensive unit tests for the API Debugger library.
"""

import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import sys

# Add the api_debugger package to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from api_debugger import (
    APIClient, 
    APIDebuggerConfig, 
    configure, 
    ConfigurationError,
    ClientError,
    RetryExhausted
)
from api_debugger.utils import (
    mask_sensitive_data,
    generate_curl_command,
    truncate_body,
    format_json,
    sanitize_url,
    get_content_type,
    is_json_content,
    format_duration,
    Timer
)
from api_debugger.logger import APIDebuggerLogger, get_logger, reset_logger
from api_debugger.config import reset_config


class TestAPIDebuggerConfig:
    """Test configuration management."""
    
    def setup_method(self):
        """Reset configuration before each test."""
        reset_config()
        # Clear environment variables
        env_vars = [k for k in os.environ.keys() if k.startswith('API_DEBUGGER_')]
        for var in env_vars:
            del os.environ[var]
    
    def test_default_config(self):
        """Test default configuration values."""
        config = APIDebuggerConfig()
        
        assert config.enabled is True
        assert config.pretty is True
        assert config.curl is True
        assert config.max_retries == 3
        assert config.timeout == 30
        assert "password" in config.mask_fields
        assert "Authorization" in config.mask_fields
    
    def test_config_from_dict(self):
        """Test creating config from dictionary."""
        config_dict = {
            "enabled": False,
            "pretty": False,
            "mask_fields": ["secret"],
            "max_retries": 5
        }
        
        config = APIDebuggerConfig.from_dict(config_dict)
        
        assert config.enabled is False
        assert config.pretty is False
        assert config.mask_fields == ["secret"]
        assert config.max_retries == 5
        # Default values should still be present
        assert config.timeout == 30
    
    def test_config_from_env(self):
        """Test creating config from environment variables."""
        os.environ['API_DEBUGGER_ENABLED'] = 'false'
        os.environ['API_DEBUGGER_MAX_RETRIES'] = '10'
        os.environ['API_DEBUGGER_MASK_FIELDS'] = 'token,secret'
        
        config = APIDebuggerConfig.from_env()
        
        assert config.enabled is False
        assert config.max_retries == 10
        assert config.mask_fields == ['token', 'secret']
    
    def test_config_validation(self):
        """Test configuration validation."""
        # Invalid log_to value
        with pytest.raises(ConfigurationError):
            APIDebuggerConfig(log_to="invalid")
        
        # Invalid max_retries
        with pytest.raises(ConfigurationError):
            APIDebuggerConfig(max_retries=-1)
        
        # Missing log_file when required
        with pytest.raises(ConfigurationError):
            APIDebuggerConfig(log_to="file", log_file=None)
    
    def test_configure_global(self):
        """Test global configuration."""
        config = configure(enabled=False, max_retries=5)
        
        assert config.enabled is False
        assert config.max_retries == 5
        
        # Test getting the same config
        from api_debugger.config import get_config
        retrieved_config = get_config()
        assert retrieved_config.enabled is False
        assert retrieved_config.max_retries == 5


class TestUtils:
    """Test utility functions."""
    
    def test_mask_sensitive_data(self):
        """Test masking of sensitive data."""
        data = {
            "username": "john",
            "password": "secret123", 
            "Authorization": "Bearer token123",
            "normal_field": "value"
        }
        
        masked = mask_sensitive_data(data, ["password", "Authorization"])
        
        assert masked["username"] == "john"
        assert masked["normal_field"] == "value" 
        assert masked["password"].startswith("se")
        assert "*" in masked["password"]
        assert masked["Authorization"].startswith("Be")
        assert "*" in masked["Authorization"]
    
    def test_mask_nested_data(self):
        """Test masking of nested data structures."""
        data = {
            "user": {
                "name": "john",
                "password": "secret"
            },
            "tokens": [
                {"token": "abc123"},
                {"token": "def456"}
            ]
        }
        
        masked = mask_sensitive_data(data, ["password", "token"])
        
        assert masked["user"]["name"] == "john"
        assert "*" in masked["user"]["password"]
        assert "*" in masked["tokens"][0]["token"]
        assert "*" in masked["tokens"][1]["token"]
    
    def test_generate_curl_command(self):
        """Test cURL command generation."""
        curl = generate_curl_command(
            method="POST",
            url="https://api.example.com/users",
            headers={"Content-Type": "application/json"},
            data='{"name": "john"}',
            params={"include": "profile"}
        )
        
        assert "curl -X POST" in curl
        assert "https://api.example.com/users" in curl
        assert "Content-Type: application/json" in curl
        assert '{"name": "john"}' in curl
        assert "include=profile" in curl
    
    def test_truncate_body(self):
        """Test body truncation."""
        short_body = "short content"
        long_body = "a" * 1000
        
        # Short body should not be truncated
        result = truncate_body(short_body, max_length=500)
        assert result == short_body
        
        # Long body should be truncated
        result = truncate_body(long_body, max_length=500)
        assert len(result) > 500  # Includes truncation message
        assert "TRUNCATED" in result
    
    def test_format_json(self):
        """Test JSON formatting."""
        data = {"name": "john", "age": 30}
        formatted = format_json(data)
        
        assert '"name"' in formatted
        assert '"john"' in formatted
        assert "\n" in formatted  # Should be pretty printed
    
    def test_sanitize_url(self):
        """Test URL sanitization."""
        url = "https://api.example.com/users?password=secret&name=john"
        sanitized = sanitize_url(url, ["password"])
        
        assert "name=john" in sanitized
        assert "password=secret" not in sanitized
        assert "MASKED" in sanitized
    
    def test_get_content_type(self):
        """Test content type extraction."""
        headers = {"Content-Type": "application/json; charset=utf-8"}
        content_type = get_content_type(headers)
        
        assert content_type == "application/json"
    
    def test_is_json_content(self):
        """Test JSON content detection."""
        assert is_json_content("application/json")
        assert is_json_content("application/vnd.api+json")
        assert not is_json_content("text/html")
        assert not is_json_content("image/png")
    
    def test_format_duration(self):
        """Test duration formatting."""
        assert "μs" in format_duration(0.0001)
        assert "ms" in format_duration(0.1)
        assert "s" in format_duration(1.5)
    
    def test_timer(self):
        """Test Timer context manager."""
        import time
        
        with Timer() as timer:
            time.sleep(0.01)  # Sleep for 10ms
        
        assert timer.duration > 0.005  # Should be at least 5ms
        assert timer.get_duration() > 0.005


class TestAPIDebuggerLogger:
    """Test logging functionality."""
    
    def setup_method(self):
        """Reset logger before each test."""
        reset_logger()
        reset_config()
    
    def test_logger_creation(self):
        """Test logger creation."""
        logger = APIDebuggerLogger()
        assert logger.name == "api_debugger"
        assert logger._logger is not None
    
    def test_get_logger_singleton(self):
        """Test logger singleton behavior."""
        logger1 = get_logger()
        logger2 = get_logger()
        
        assert logger1 is logger2
    
    def test_log_request(self):
        """Test request logging."""
        configure(enabled=True, pretty=False)  # Use plain logging for testing
        logger = get_logger()
        
        # Mock the internal logger to capture output
        with patch.object(logger._logger, 'debug') as mock_debug:
            logger.log_request(
                method="GET",
                url="https://api.example.com/users",
                headers={"Authorization": "Bearer token"},
                body=None
            )
            
            mock_debug.assert_called_once()
            log_message = mock_debug.call_args[0][0]
            assert "GET" in log_message
            assert "https://api.example.com/users" in log_message
    
    def test_log_response(self):
        """Test response logging."""
        configure(enabled=True, pretty=False)
        logger = get_logger()
        
        with patch.object(logger._logger, 'debug') as mock_debug:
            logger.log_response(
                status_code=200,
                headers={"Content-Type": "application/json"},
                body='{"success": true}',
                duration=0.5
            )
            
            mock_debug.assert_called_once()
            log_message = mock_debug.call_args[0][0]
            assert "200" in log_message
            assert "0.50s" in log_message


class TestAPIClient:
    """Test API client functionality."""
    
    def setup_method(self):
        """Reset configuration before each test."""
        reset_config()
    
    @patch('api_debugger.client.requests')
    def test_client_creation_requests(self, mock_requests):
        """Test client creation with requests backend."""
        mock_requests.Session.return_value = Mock()
        
        client = APIClient(
            base_url="https://api.example.com",
            backend="requests"
        )
        
        assert client.backend == "requests"
        assert client.base_url == "https://api.example.com"
    
    @patch('api_debugger.client.httpx')
    def test_client_creation_httpx(self, mock_httpx):
        """Test client creation with httpx backend."""
        mock_httpx.Client.return_value = Mock()
        
        client = APIClient(
            base_url="https://api.example.com",
            backend="httpx"
        )
        
        assert client.backend == "httpx"
    
    def test_build_url(self):
        """Test URL building."""
        client = APIClient(base_url="https://api.example.com")
        
        # Relative URL
        url = client._build_url("users")
        assert url == "https://api.example.com/users"
        
        # Absolute URL
        url = client._build_url("https://other-api.com/data")
        assert url == "https://other-api.com/data"
        
        # URL with leading slash
        url = client._build_url("/users")
        assert url == "https://api.example.com/users"
    
    @patch('api_debugger.client.requests')
    def test_request_with_retry(self, mock_requests):
        """Test request with retry mechanism."""
        # Mock session and response
        mock_session = Mock()
        mock_requests.Session.return_value = mock_session
        
        # First two calls fail, third succeeds
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {}
        mock_response.text = "success"
        mock_response.url = "https://api.example.com/users"
        
        mock_session.request.side_effect = [
            ConnectionError("Connection failed"),
            ConnectionError("Connection failed"), 
            mock_response
        ]
        
        configure(max_retries=3, retry_delay=0.01)  # Fast retry for testing
        client = APIClient(backend="requests", debug=False)  # Disable debug to avoid logging
        
        response = client.get("https://api.example.com/users")
        
        assert response.status_code == 200
        assert mock_session.request.call_count == 3  # 2 failures + 1 success
    
    @patch('api_debugger.client.requests')
    def test_request_retry_exhausted(self, mock_requests):
        """Test request when all retries are exhausted."""
        mock_session = Mock()
        mock_requests.Session.return_value = mock_session
        
        mock_session.request.side_effect = ConnectionError("Connection failed")
        
        configure(max_retries=2, retry_delay=0.01)
        client = APIClient(backend="requests", debug=False)
        
        with pytest.raises(RetryExhausted) as exc_info:
            client.get("https://api.example.com/users")
        
        assert exc_info.value.attempts == 3  # 2 retries + 1 initial attempt
        assert mock_session.request.call_count == 3
    
    def test_context_manager(self):
        """Test client as context manager."""
        with patch('api_debugger.client.requests') as mock_requests:
            mock_session = Mock()
            mock_requests.Session.return_value = mock_session
            
            with APIClient(backend="requests") as client:
                assert client is not None
            
            # Should call close on exit
            mock_session.close.assert_called_once()


class TestMiddleware:
    """Test middleware components."""
    
    def test_django_middleware_import(self):
        """Test Django middleware import."""
        try:
            from api_debugger.django_middleware import APIDebuggerMiddleware
            # If Django is not available, the class should still be importable
            # but will raise an error when instantiated
        except ImportError:
            pytest.fail("Should be able to import Django middleware")
    
    def test_fastapi_middleware_import(self):
        """Test FastAPI middleware import."""
        try:
            from api_debugger.fastapi_middleware import APIDebuggerMiddleware
            # If FastAPI is not available, the class should still be importable
            # but will raise an error when instantiated  
        except ImportError:
            pytest.fail("Should be able to import FastAPI middleware")


class TestIntegration:
    """Integration tests."""
    
    def test_end_to_end_configuration(self):
        """Test end-to-end configuration flow."""
        # Set up environment
        os.environ['API_DEBUGGER_ENABLED'] = 'true'
        os.environ['API_DEBUGGER_MASK_FIELDS'] = 'password,secret'
        
        try:
            # Load config from environment
            config = APIDebuggerConfig.from_env()
            
            # Create client with config
            with patch('api_debugger.client.requests') as mock_requests:
                mock_session = Mock()
                mock_requests.Session.return_value = mock_session
                
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.headers = {}
                mock_response.text = '{"success": true}'
                mock_response.url = "https://api.example.com/test"
                mock_session.request.return_value = mock_response
                
                client = APIClient(config=config, backend="requests", debug=False)
                response = client.get("https://api.example.com/test")
                
                assert response.status_code == 200
                
        finally:
            # Clean up environment
            if 'API_DEBUGGER_ENABLED' in os.environ:
                del os.environ['API_DEBUGGER_ENABLED']
            if 'API_DEBUGGER_MASK_FIELDS' in os.environ:
                del os.environ['API_DEBUGGER_MASK_FIELDS']
    
    def test_file_logging(self):
        """Test logging to file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            log_file = f.name
        
        try:
            configure(
                enabled=True,
                log_to="file",
                log_file=log_file,
                pretty=False
            )
            
            logger = get_logger()
            logger.log_info("Test message")
            
            # Check that log file exists and has content
            assert Path(log_file).exists()
            
            with open(log_file, 'r') as f:
                content = f.read()
                assert "Test message" in content
                
        finally:
            # Clean up
            if Path(log_file).exists():
                Path(log_file).unlink()


if __name__ == "__main__":
    # Run specific tests for development
    pytest.main([__file__, "-v"])