"""
Configuration management for API Debugger.
"""

import os
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from .exceptions import ConfigurationError


@dataclass
class APIDebuggerConfig:
    """Configuration class for API Debugger settings."""
    
    enabled: bool = True
    mask_fields: List[str] = field(default_factory=lambda: ["password", "Authorization", "token", "secret"])
    log_to: str = "console"  # Options: console, file, both
    log_file: Optional[str] = None
    pretty: bool = True
    curl: bool = True
    max_retries: int = 3
    retry_delay: float = 1.0
    timeout: int = 30
    log_level: str = "DEBUG"
    max_body_length: int = 10000  # Maximum length of request/response body to log
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        if self.log_to not in ["console", "file", "both"]:
            raise ConfigurationError(f"Invalid log_to value: {self.log_to}")
        
        if self.log_to in ["file", "both"] and not self.log_file:
            raise ConfigurationError("log_file must be specified when log_to is 'file' or 'both'")
        
        if self.max_retries < 0:
            raise ConfigurationError("max_retries must be >= 0")
        
        if self.retry_delay < 0:
            raise ConfigurationError("retry_delay must be >= 0")
        
        if self.timeout <= 0:
            raise ConfigurationError("timeout must be > 0")
        
        if self.log_level not in ["DEBUG", "INFO", "WARNING", "ERROR"]:
            raise ConfigurationError(f"Invalid log_level: {self.log_level}")

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'APIDebuggerConfig':
        """Create configuration from dictionary."""
        return cls(**config_dict)
    
    @classmethod
    def from_env(cls) -> 'APIDebuggerConfig':
        """Create configuration from environment variables."""
        config = {}
        
        # Boolean settings
        if os.getenv('API_DEBUGGER_ENABLED'):
            config['enabled'] = os.getenv('API_DEBUGGER_ENABLED', 'true').lower() == 'true'
        
        if os.getenv('API_DEBUGGER_PRETTY'):
            config['pretty'] = os.getenv('API_DEBUGGER_PRETTY', 'true').lower() == 'true'
        
        if os.getenv('API_DEBUGGER_CURL'):
            config['curl'] = os.getenv('API_DEBUGGER_CURL', 'true').lower() == 'true'
        
        # String settings
        if os.getenv('API_DEBUGGER_LOG_TO'):
            config['log_to'] = os.getenv('API_DEBUGGER_LOG_TO')
        
        if os.getenv('API_DEBUGGER_LOG_FILE'):
            config['log_file'] = os.getenv('API_DEBUGGER_LOG_FILE')
        
        if os.getenv('API_DEBUGGER_LOG_LEVEL'):
            config['log_level'] = os.getenv('API_DEBUGGER_LOG_LEVEL')
        
        # Integer settings
        if os.getenv('API_DEBUGGER_MAX_RETRIES'):
            config['max_retries'] = int(os.getenv('API_DEBUGGER_MAX_RETRIES'))
        
        if os.getenv('API_DEBUGGER_TIMEOUT'):
            config['timeout'] = int(os.getenv('API_DEBUGGER_TIMEOUT'))
        
        if os.getenv('API_DEBUGGER_MAX_BODY_LENGTH'):
            config['max_body_length'] = int(os.getenv('API_DEBUGGER_MAX_BODY_LENGTH'))
        
        # Float settings
        if os.getenv('API_DEBUGGER_RETRY_DELAY'):
            config['retry_delay'] = float(os.getenv('API_DEBUGGER_RETRY_DELAY'))
        
        # List settings
        if os.getenv('API_DEBUGGER_MASK_FIELDS'):
            config['mask_fields'] = os.getenv('API_DEBUGGER_MASK_FIELDS').split(',')
        
        return cls(**config)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            'enabled': self.enabled,
            'mask_fields': self.mask_fields,
            'log_to': self.log_to,
            'log_file': self.log_file,
            'pretty': self.pretty,
            'curl': self.curl,
            'max_retries': self.max_retries,
            'retry_delay': self.retry_delay,
            'timeout': self.timeout,
            'log_level': self.log_level,
            'max_body_length': self.max_body_length,
        }


# Global configuration instance
_global_config: Optional[APIDebuggerConfig] = None


def configure(
    config: Optional[Union[Dict[str, Any], APIDebuggerConfig]] = None,
    **kwargs
) -> APIDebuggerConfig:
    """
    Configure global API Debugger settings.
    
    Args:
        config: Configuration dictionary or APIDebuggerConfig instance
        **kwargs: Individual configuration parameters
    
    Returns:
        The configured APIDebuggerConfig instance
    """
    global _global_config
    
    if config is None:
        # Use kwargs if no config provided
        _global_config = APIDebuggerConfig(**kwargs)
    elif isinstance(config, dict):
        # Merge config dict with kwargs
        merged_config = {**config, **kwargs}
        _global_config = APIDebuggerConfig.from_dict(merged_config)
    elif isinstance(config, APIDebuggerConfig):
        # Use provided config but override with kwargs
        config_dict = config.to_dict()
        merged_config = {**config_dict, **kwargs}
        _global_config = APIDebuggerConfig.from_dict(merged_config)
    else:
        raise ConfigurationError(f"Invalid config type: {type(config)}")
    
    return _global_config


def get_config() -> APIDebuggerConfig:
    """
    Get the current global configuration.
    
    Returns:
        The current APIDebuggerConfig instance
    """
    global _global_config
    
    if _global_config is None:
        # Try to load from environment variables first
        try:
            _global_config = APIDebuggerConfig.from_env()
        except Exception:
            # Fall back to default configuration
            _global_config = APIDebuggerConfig()
    
    return _global_config


def reset_config():
    """Reset the global configuration to None."""
    global _global_config
    _global_config = None