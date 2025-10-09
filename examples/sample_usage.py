"""
Sample usage examples for API Debugger.

This script demonstrates how to use the API Debugger library in various scenarios:
1. Basic API client usage
2. Django REST Framework middleware integration
3. FastAPI middleware integration
4. Configuration options
"""

import os
import sys
import asyncio
import json
from pathlib import Path

# Add the api_debugger package to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from api_debugger import APIClient, configure, APIDebuggerConfig


def example_1_basic_client():
    """Example 1: Basic API Client Usage"""
    print("=" * 60)
    print("EXAMPLE 1: Basic API Client Usage")
    print("=" * 60)
    
    # Configure global settings
    configure(
        enabled=True,
        pretty=True,
        curl=True,
        mask_fields=["password", "Authorization", "token"]
    )
    
    # Create API client
    client = APIClient(
        base_url="https://jsonplaceholder.typicode.com",
        debug=True
    )
    
    try:
        # GET request
        print("\n--- Making GET request ---")
        response = client.get("/posts/1")
        print(f"Status: {response.status_code}")
        
        # POST request with JSON data
        print("\n--- Making POST request ---")
        post_data = {
            "title": "Test Post",
            "body": "This is a test post body",
            "userId": 1,
            "password": "secret123"  # This should be masked in logs
        }
        response = client.post("/posts", json=post_data)
        print(f"Status: {response.status_code}")
        
    except Exception as e:
        print(f"Request failed: {e}")
    
    finally:
        client.close()


def example_2_configuration_options():
    """Example 2: Different Configuration Options"""
    print("\n" + "=" * 60)
    print("EXAMPLE 2: Configuration Options")
    print("=" * 60)
    
    # Example with file logging
    config = APIDebuggerConfig(
        enabled=True,
        log_to="both",  # Log to both console and file
        log_file="/tmp/api_debug.log",
        pretty=False,   # Use plain text logging
        curl=True,
        max_retries=2,
        retry_delay=0.5,
        mask_fields=["secret", "password", "token", "auth"]
    )
    
    client = APIClient(
        base_url="https://httpbin.org",
        debug=True,
        config=config
    )
    
    try:
        # Request with authentication header (should be masked)
        headers = {
            "Authorization": "Bearer super-secret-token",
            "Content-Type": "application/json"
        }
        
        print("\n--- Request with masked headers ---")
        response = client.post(
            "/post", 
            headers=headers,
            json={"message": "Hello World", "secret": "top-secret-data"}
        )
        print(f"Status: {response.status_code}")
        
    except Exception as e:
        print(f"Request failed: {e}")
    
    finally:
        client.close()
        
        # Show log file contents if it exists
        log_file = Path("/tmp/api_debug.log")
        if log_file.exists():
            print(f"\n--- Log file contents ({log_file}) ---")
            with open(log_file, "r") as f:
                print(f.read()[-500:])  # Show last 500 characters


def example_3_retry_mechanism():
    """Example 3: Retry Mechanism"""
    print("\n" + "=" * 60)
    print("EXAMPLE 3: Retry Mechanism")
    print("=" * 60)
    
    config = APIDebuggerConfig(
        enabled=True,
        pretty=True,
        max_retries=3,
        retry_delay=1.0
    )
    
    client = APIClient(
        base_url="https://httpbin.org",
        debug=True,
        config=config
    )
    
    try:
        # This should trigger retries (status code 500)
        print("\n--- Request that will fail and retry ---")
        response = client.get("/status/500")
        print(f"Status: {response.status_code}")
        
    except Exception as e:
        print(f"Request failed after retries: {e}")
    
    finally:
        client.close()


def example_4_django_middleware():
    """Example 4: Django Middleware Usage"""
    print("\n" + "=" * 60)
    print("EXAMPLE 4: Django Middleware Usage")
    print("=" * 60)
    
    print("""
To use the Django middleware, add it to your Django settings:

# settings.py
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    # ... other middleware ...
    'api_debugger.django_middleware.APIDebuggerMiddleware',  # Add this
    'django.middleware.common.CommonMiddleware',
    # ... rest of middleware ...
]

# Optional: Configure API Debugger settings
API_DEBUGGER = {
    "enabled": True,
    "mask_fields": ["password", "Authorization", "secret"],
    "log_to": "console",
    "pretty": True,
    "curl": True,
    "max_body_length": 5000
}

The middleware will automatically log all incoming requests and outgoing responses
with timing information, headers, and optionally cURL commands.
""")
    
    # Show a mock Django request/response
    print("\n--- Mock Django Request/Response Log ---")
    print("""
🚀 HTTP REQUEST - POST
URL: /api/users/
Headers:
  Content-Type: application/json
  Authorization: Bearer to**********
Body:
{
  "username": "john_doe",
  "email": "john@example.com",  
  "password": "***MASKED***"
}
cURL: curl -X POST "https://example.com/api/users/" -H "Content-Type: application/json" -H "Authorization: Bearer to**********" -d '{"username": "john_doe", "email": "john@example.com", "password": "***MASKED***"}'

✅ HTTP RESPONSE - 201 (45.2ms)
Headers:
  Content-Type: application/json
  Location: /api/users/123/
Body:
{
  "id": 123,
  "username": "john_doe",
  "email": "john@example.com",
  "created_at": "2024-01-15T10:30:00Z"
}
""")


def example_5_fastapi_middleware():
    """Example 5: FastAPI Middleware Usage"""
    print("\n" + "=" * 60)
    print("EXAMPLE 5: FastAPI Middleware Usage")
    print("=" * 60)
    
    print("""
To use the FastAPI middleware, add it to your FastAPI app:

# main.py
from fastapi import FastAPI
from api_debugger import FastAPIMiddleware

app = FastAPI()

# Add the API Debugger middleware
app.add_middleware(FastAPIMiddleware, config={
    "enabled": True,
    "mask_fields": ["password", "Authorization", "secret"],
    "log_to": "console", 
    "pretty": True,
    "curl": True
})

@app.post("/api/users/")
async def create_user(user_data: dict):
    return {"id": 123, "username": user_data["username"]}

# Alternative: Use environment variables for configuration
# Set these environment variables:
# API_DEBUGGER_ENABLED=true
# API_DEBUGGER_MASK_FIELDS=password,Authorization,secret
# API_DEBUGGER_PRETTY=true
# API_DEBUGGER_CURL=true

# Then just add the middleware without config:
# app.add_middleware(FastAPIMiddleware)
""")
    
    # Show async example if available
    try:
        import asyncio
        print("\n--- Async Client Example ---")
        
        async def async_example():
            # This would be used with an async HTTP client
            print("In a real scenario, you would:")
            print("1. Start your FastAPI server with the middleware")
            print("2. Make requests to your API endpoints")
            print("3. See detailed logging in your console/logs")
        
        asyncio.run(async_example())
        
    except ImportError:
        print("\nAsyncio not available for async example")


def example_6_environment_configuration():
    """Example 6: Environment Variable Configuration"""
    print("\n" + "=" * 60)
    print("EXAMPLE 6: Environment Variable Configuration")
    print("=" * 60)
    
    # Set environment variables (in real usage, set these in your shell)
    os.environ['API_DEBUGGER_ENABLED'] = 'true'
    os.environ['API_DEBUGGER_PRETTY'] = 'true'
    os.environ['API_DEBUGGER_CURL'] = 'false'
    os.environ['API_DEBUGGER_MASK_FIELDS'] = 'password,secret,token,auth'
    os.environ['API_DEBUGGER_MAX_RETRIES'] = '2'
    os.environ['API_DEBUGGER_LOG_LEVEL'] = 'INFO'
    
    # Load configuration from environment
    config = APIDebuggerConfig.from_env()
    print(f"Loaded config from environment:")
    print(f"  Enabled: {config.enabled}")
    print(f"  Pretty: {config.pretty}")
    print(f"  cURL: {config.curl}")
    print(f"  Mask fields: {config.mask_fields}")
    print(f"  Max retries: {config.max_retries}")
    print(f"  Log level: {config.log_level}")
    
    # Use the environment-based config
    client = APIClient(
        base_url="https://httpbin.org",
        debug=True,
        config=config
    )
    
    try:
        print("\n--- Using environment configuration ---")
        response = client.get("/get", params={"test": "environment_config"})
        print(f"Status: {response.status_code}")
        
    except Exception as e:
        print(f"Request failed: {e}")
    
    finally:
        client.close()


def main():
    """Run all examples"""
    print("API DEBUGGER - USAGE EXAMPLES")
    print("This script demonstrates various features of the API Debugger library.\n")
    
    try:
        example_1_basic_client()
        example_2_configuration_options()
        # Skip retry example to avoid waiting
        # example_3_retry_mechanism() 
        example_4_django_middleware()
        example_5_fastapi_middleware()
        example_6_environment_configuration()
        
        print("\n" + "=" * 60)
        print("ALL EXAMPLES COMPLETED")
        print("=" * 60)
        print("\nFor more information, see the README.md file.")
        
    except KeyboardInterrupt:
        print("\nExamples interrupted by user")
    except Exception as e:
        print(f"\nError running examples: {e}")


if __name__ == "__main__":
    main()