# API Debugger

[![PyPI version](https://badge.fury.io/py/api-debugger.svg)](https://badge.fury.io/py/api-debugger)
[![Python versions](https://img.shields.io/pypi/pyversions/api-debugger.svg)](https://pypi.org/project/api-debugger/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://github.com/yourusername/api-debugger/workflows/Tests/badge.svg)](https://github.com/yourusername/api-debugger/actions)

A comprehensive Python library for debugging API calls with beautiful logging, cURL export, and seamless integrations for Django REST Framework and FastAPI.

## 🌟 Features

### 🚀 Standalone API Client
- **Beautiful Debug Logging**: Rich, colored console output with request/response details
- **cURL Export**: Generate equivalent cURL commands for any request
- **Smart Retry Logic**: Configurable retry mechanism with exponential backoff
- **Data Masking**: Automatically mask sensitive fields in logs
- **Multiple Backends**: Support for both `requests` and `httpx` HTTP libraries
- **Flexible Configuration**: Environment variables, dictionaries, or programmatic setup

### 🔧 Framework Integrations
- **Django REST Framework**: Drop-in middleware for automatic API logging
- **FastAPI**: ASGI middleware for async API debugging
- **Zero Configuration**: Works out of the box with sensible defaults
- **Production Ready**: Toggle debugging on/off via environment variables

### 📊 Rich Logging Features
- **Pretty JSON Formatting**: Syntax-highlighted JSON in logs
- **Request/Response Timing**: Precise duration measurements
- **HTTP Status Colors**: Visual status code indicators
- **Configurable Output**: Console, file, or both
- **Log Level Control**: Fine-tune logging verbosity

## 📦 Installation

```bash
# Basic installation
pip install api-debugger

# With specific HTTP backend
pip install api-debugger[requests]  # or [httpx]

# With rich formatting
pip install api-debugger[rich]

# With framework integrations
pip install api-debugger[django]    # or [fastapi]

# Install everything
pip install api-debugger[full]
```

## 🚀 Quick Start

### Basic API Client Usage

```python
from api_debugger import APIClient, configure

# Configure global settings
configure(
    enabled=True,
    pretty=True, 
    curl=True,
    mask_fields=["password", "Authorization", "token"]
)

# Create and use the client
with APIClient("https://jsonplaceholder.typicode.com") as client:
    # GET request
    response = client.get("/posts/1")
    
    # POST request with JSON
    response = client.post("/posts", json={
        "title": "Test Post",
        "body": "This is a test",
        "userId": 1
    })
    
    # Request with authentication (will be masked in logs)
    client.set_default_headers({
        "Authorization": "Bearer your-secret-token"
    })
    response = client.get("/user/profile")
```

### Django REST Framework Integration

```python
# settings.py
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    # Add API Debugger middleware
    'api_debugger.django_middleware.APIDebuggerMiddleware',
    'django.middleware.common.CommonMiddleware',
    # ... rest of your middleware
]

# Optional: Configure API Debugger
API_DEBUGGER = {
    "enabled": True,
    "mask_fields": ["password", "Authorization", "secret"],
    "log_to": "console",  # "console", "file", or "both"
    "pretty": True,
    "curl": True,
    "max_body_length": 10000
}
```

### FastAPI Integration

```python
from fastapi import FastAPI
from api_debugger import FastAPIMiddleware

app = FastAPI()

# Add API Debugger middleware
app.add_middleware(FastAPIMiddleware, config={
    "enabled": True,
    "mask_fields": ["password", "Authorization"],
    "pretty": True,
    "curl": True
})

@app.post("/users/")
async def create_user(user_data: dict):
    return {"id": 123, "username": user_data["username"]}

# Alternative: Use environment variables
# Just add: app.add_middleware(FastAPIMiddleware)
# Then set: API_DEBUGGER_ENABLED=true
```

## 🔧 Configuration

### Environment Variables

```bash
# Enable/disable debugging
export API_DEBUGGER_ENABLED=true

# Output formatting
export API_DEBUGGER_PRETTY=true
export API_DEBUGGER_CURL=true

# Logging destination
export API_DEBUGGER_LOG_TO=console  # or "file" or "both"
export API_DEBUGGER_LOG_FILE=/path/to/debug.log

# Data masking
export API_DEBUGGER_MASK_FIELDS=password,Authorization,token,secret

# Retry configuration
export API_DEBUGGER_MAX_RETRIES=3
export API_DEBUGGER_RETRY_DELAY=1.0
export API_DEBUGGER_TIMEOUT=30

# Log verbosity
export API_DEBUGGER_LOG_LEVEL=DEBUG  # DEBUG, INFO, WARNING, ERROR
```

### Programmatic Configuration

```python
from api_debugger import configure, APIDebuggerConfig

# Method 1: Using configure function
configure(
    enabled=True,
    mask_fields=["password", "secret"],
    log_to="both",
    log_file="/tmp/api_debug.log",
    pretty=True,
    curl=True,
    max_retries=5,
    retry_delay=2.0
)

# Method 2: Using config object
config = APIDebuggerConfig(
    enabled=True,
    pretty=True,
    mask_fields=["auth_token", "password"]
)

client = APIClient("https://api.example.com", config=config)
```

## 📖 Examples

### Request with Retry Logic

```python
from api_debugger import APIClient, configure

configure(max_retries=3, retry_delay=1.0)

with APIClient("https://unreliable-api.com") as client:
    try:
        response = client.get("/flaky-endpoint")
        print(f"Success after retries: {response.status_code}")
    except RetryExhausted as e:
        print(f"Failed after {e.attempts} attempts: {e.last_exception}")
```

### Custom Data Masking

```python
config = APIDebuggerConfig(
    mask_fields=["credit_card", "ssn", "api_key", "password"]
)

client = APIClient(config=config)
response = client.post("/payment", json={
    "amount": 100,
    "credit_card": "1234-5678-9012-3456",  # Will be masked
    "description": "Purchase"  # Will be visible
})
```

### File and Console Logging

```python
configure(
    log_to="both",
    log_file="/var/log/api_debug.log",
    pretty=True  # Pretty format for console, plain for file
)

client = APIClient("https://api.example.com")
# All requests will be logged to both console and file
```

## 🎨 Output Examples

### Console Output (Pretty Mode)

```
🚀 HTTP REQUEST - POST
URL: https://api.example.com/users
Headers:
  Content-Type: application/json  
  Authorization: Bearer to**********
Body:
{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "***MASKED***"
}
cURL: curl -X POST "https://api.example.com/users" -H "Content-Type: application/json" -d '{"username": "john_doe", "email": "john@example.com", "password": "***MASKED***"}'

✅ HTTP RESPONSE - 201 (234ms)
Headers:
  Content-Type: application/json
Body:
{
  "id": 123,
  "username": "john_doe", 
  "created_at": "2024-01-15T10:30:00Z"
}
```

### Plain Text Output

```
=== HTTP REQUEST - GET ===
URL: https://api.example.com/posts/1
Headers:
  Authorization: Bearer to**********
  User-Agent: api-debugger/1.0.0
cURL: curl -X GET "https://api.example.com/posts/1" -H "Authorization: Bearer to**********"

=== HTTP RESPONSE - 200 ===
Duration: 145ms
Headers:
  Content-Type: application/json
Body:
{"id": 1, "title": "Sample Post", "body": "Post content..."}
==================================================
```

## 🧪 Testing

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=api_debugger --cov-report=html

# Run specific test categories
pytest -m "not slow"  # Skip slow tests
pytest -m integration  # Run only integration tests
```

## 🗺️ Roadmap

### v0.1.0 - Initial Release ✅
- [x] Core API client with debugging
- [x] Django REST Framework middleware
- [x] FastAPI middleware  
- [x] Basic configuration system
- [x] Request/response logging
- [x] cURL command export
- [x] Data masking for sensitive fields

### v0.2.0 - Enhanced Features
- [ ] **Performance Metrics**: Response time histograms, throughput tracking
- [ ] **Advanced Filtering**: Log only specific status codes or endpoints
- [ ] **Request/Response Hooks**: Custom processing before/after logging
- [ ] **Async Client Support**: Native async/await API client
- [ ] **Structured Logging**: JSON-structured logs for machine parsing

### v0.3.0 - Integrations & Extensions
- [ ] **Flask Integration**: Middleware for Flask applications
- [ ] **Requests Session Integration**: Drop-in replacement for requests.Session
- [ ] **Custom Formatters**: Pluggable output formatters (JSON, XML, etc.)
- [ ] **Webhook Notifications**: Send debug info to external services
- [ ] **CLI Tool**: Command-line interface for API testing

### v1.0.0 - Production Ready
- [ ] **Advanced Retry Strategies**: Exponential backoff, jitter, circuit breaker
- [ ] **Rate Limiting Integration**: Built-in rate limiting with debugging
- [ ] **Metrics Export**: Prometheus, StatsD, CloudWatch integration
- [ ] **Request Correlation**: Trace requests across microservices
- [ ] **Performance Optimizations**: Minimal overhead for production use

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/api-debugger.git
cd api-debugger

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\\Scripts\\activate` on Windows

# Install in development mode
pip install -e ".[dev]"

# Run pre-commit hooks
pre-commit install
```

### Running Examples

```bash
# Run the example script
python examples/sample_usage.py

# Test Django middleware (requires Django)
cd examples/django_example
python manage.py runserver

# Test FastAPI middleware (requires FastAPI)
cd examples/fastapi_example  
uvicorn main:app --reload
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: [https://api-debugger.readthedocs.io/](https://api-debugger.readthedocs.io/)
- **Bug Reports**: [GitHub Issues](https://github.com/yourusername/api-debugger/issues)
- **Feature Requests**: [GitHub Discussions](https://github.com/yourusername/api-debugger/discussions)
- **Security Issues**: Please email security@example.com

## 🙏 Acknowledgments

- [requests](https://github.com/psf/requests) - The elegant HTTP library
- [httpx](https://github.com/encode/httpx) - A next-generation HTTP client
- [rich](https://github.com/Textualize/rich) - Rich text and beautiful formatting
- [Django](https://github.com/django/django) - The web framework for perfectionists
- [FastAPI](https://github.com/tiangolo/fastapi) - Modern, fast web framework

---

<p align="center">
  Made with ❤️ by the API Debugger Team
</p>