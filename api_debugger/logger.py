"""
Logging utilities for API Debugger with rich formatting support.
"""

import logging
import sys
from typing import Dict, Optional
from pathlib import Path

try:
    from rich.console import Console
    from rich.logging import RichHandler
    from rich.panel import Panel
    from rich.syntax import Syntax
    from rich.table import Table
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

from .config import get_config
from .utils import format_json, truncate_body, format_duration, mask_sensitive_data, get_content_type, is_json_content


class APIDebuggerLogger:
    """Logger for API debugging with rich formatting support."""
    
    def __init__(self, name: str = "api_debugger"):
        self.name = name
        self.config = get_config()
        self._logger = None
        self._console = None
        self._setup_logger()
    
    def _setup_logger(self):
        """Set up the logger based on configuration."""
        self._logger = logging.getLogger(self.name)
        self._logger.setLevel(getattr(logging, self.config.log_level))
        
        # Clear existing handlers
        self._logger.handlers.clear()
        
        # Set up console handler
        if self.config.log_to in ["console", "both"]:
            if RICH_AVAILABLE and self.config.pretty:
                console = Console(stderr=True, force_terminal=True)
                self._console = console
                console_handler = RichHandler(
                    console=console,
                    show_time=True,
                    show_path=False,
                    markup=True
                )
            else:
                console_handler = logging.StreamHandler(sys.stderr)
                formatter = logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                )
                console_handler.setFormatter(formatter)
            
            self._logger.addHandler(console_handler)
        
        # Set up file handler
        if self.config.log_to in ["file", "both"] and self.config.log_file:
            file_path = Path(self.config.log_file)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.FileHandler(self.config.log_file)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(formatter)
            self._logger.addHandler(file_handler)
    
    def log_request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        body: Optional[str] = None,
        curl_command: Optional[str] = None
    ):
        """
        Log an HTTP request.
        
        Args:
            method: HTTP method
            url: Request URL
            headers: Request headers
            body: Request body
            curl_command: cURL command equivalent
        """
        if not self.config.enabled:
            return
        
        if RICH_AVAILABLE and self.config.pretty and self._console:
            self._log_request_rich(method, url, headers, body, curl_command)
        else:
            self._log_request_plain(method, url, headers, body, curl_command)
    
    def log_response(
        self,
        status_code: int,
        headers: Optional[Dict[str, str]] = None,
        body: Optional[str] = None,
        duration: Optional[float] = None
    ):
        """
        Log an HTTP response.
        
        Args:
            status_code: HTTP status code
            headers: Response headers
            body: Response body
            duration: Request duration in seconds
        """
        if not self.config.enabled:
            return
        
        if RICH_AVAILABLE and self.config.pretty and self._console:
            self._log_response_rich(status_code, headers, body, duration)
        else:
            self._log_response_plain(status_code, headers, body, duration)
    
    def _log_request_rich(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        body: Optional[str] = None,
        curl_command: Optional[str] = None
    ):
        """Log request with rich formatting."""
        title = f"🚀 [bold cyan]HTTP REQUEST[/bold cyan] - {method.upper()}"
        
        content = []
        
        # URL
        content.append(f"[bold]URL:[/bold] {url}")
        
        # Headers
        if headers:
            masked_headers = mask_sensitive_data(headers, self.config.mask_fields)
            headers_table = Table(show_header=True, header_style="bold blue")
            headers_table.add_column("Header", style="cyan")
            headers_table.add_column("Value", style="white")
            
            for key, value in masked_headers.items():
                headers_table.add_row(key, str(value))
            
            content.append("\n[bold]Headers:[/bold]")
            content.append(headers_table)
        
        # Body
        if body:
            body = truncate_body(body, self.config.max_body_length)
            content_type = get_content_type(headers or {})
            
            if is_json_content(content_type):
                try:
                    formatted_body = format_json(body)
                    syntax = Syntax(formatted_body, "json", theme="monokai", line_numbers=False)
                    content.append("\n[bold]Body:[/bold]")
                    content.append(syntax)
                except Exception:
                    content.append(f"\n[bold]Body:[/bold]\n{body}")
            else:
                content.append(f"\n[bold]Body:[/bold]\n{body}")
        
        # cURL command
        if curl_command and self.config.curl:
            content.append(f"\n[bold]cURL:[/bold]\n[dim]{curl_command}[/dim]")
        
        # Create panel with string content only
        string_content = "\n".join([str(c) for c in content if isinstance(c, str)])
        panel = Panel(
            string_content,
            title=title,
            border_style="blue",
            padding=(1, 1)
        )
        
        self._console.print(panel)
        
        # Print tables and syntax separately
        for item in content:
            if not isinstance(item, str):
                self._console.print(item)
    
    def _log_response_rich(
        self,
        status_code: int,
        headers: Optional[Dict[str, str]] = None,
        body: Optional[str] = None,
        duration: Optional[float] = None
    ):
        """Log response with rich formatting."""
        # Color based on status code
        if 200 <= status_code < 300:
            status_color = "green"
            emoji = "✅"
        elif 300 <= status_code < 400:
            status_color = "yellow"
            emoji = "↩️"
        elif 400 <= status_code < 500:
            status_color = "orange3"
            emoji = "❌"
        else:
            status_color = "red"
            emoji = "💥"
        
        title = f"{emoji} [bold {status_color}]HTTP RESPONSE[/bold {status_color}] - {status_code}"
        
        content = []
        
        # Status and timing
        status_line = f"[bold]Status:[/bold] [{status_color}]{status_code}[/{status_color}]"
        if duration is not None:
            status_line += f" [dim]({format_duration(duration)})[/dim]"
        content.append(status_line)
        
        # Headers
        if headers:
            headers_table = Table(show_header=True, header_style="bold blue")
            headers_table.add_column("Header", style="cyan")
            headers_table.add_column("Value", style="white")
            
            for key, value in headers.items():
                headers_table.add_row(key, str(value))
            
            content.append("\n[bold]Headers:[/bold]")
            content.append(headers_table)
        
        # Body
        if body:
            body = truncate_body(body, self.config.max_body_length)
            content_type = get_content_type(headers or {})
            
            if is_json_content(content_type):
                try:
                    formatted_body = format_json(body)
                    syntax = Syntax(formatted_body, "json", theme="monokai", line_numbers=False)
                    content.append("\n[bold]Body:[/bold]")
                    content.append(syntax)
                except Exception:
                    content.append(f"\n[bold]Body:[/bold]\n{body}")
            else:
                content.append(f"\n[bold]Body:[/bold]\n{body}")
        
        # Create panel
        panel = Panel(
            "\n".join([str(c) for c in content if isinstance(c, str)]),
            title=title,
            border_style=status_color,
            padding=(1, 1)
        )
        
        self._console.print(panel)
        
        # Print tables and syntax separately
        for item in content:
            if not isinstance(item, str):
                self._console.print(item)
    
    def _log_request_plain(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        body: Optional[str] = None,
        curl_command: Optional[str] = None
    ):
        """Log request with plain formatting."""
        lines = []
        lines.append(f"=== HTTP REQUEST - {method.upper()} ===")
        lines.append(f"URL: {url}")
        
        if headers:
            masked_headers = mask_sensitive_data(headers, self.config.mask_fields)
            lines.append("Headers:")
            for key, value in masked_headers.items():
                lines.append(f"  {key}: {value}")
        
        if body:
            body = truncate_body(body, self.config.max_body_length)
            lines.append(f"Body:\n{body}")
        
        if curl_command and self.config.curl:
            lines.append(f"cURL: {curl_command}")
        
        lines.append("=" * 50)
        
        self._logger.debug("\n".join(lines))
    
    def _log_response_plain(
        self,
        status_code: int,
        headers: Optional[Dict[str, str]] = None,
        body: Optional[str] = None,
        duration: Optional[float] = None
    ):
        """Log response with plain formatting."""
        lines = []
        lines.append(f"=== HTTP RESPONSE - {status_code} ===")
        
        if duration is not None:
            lines.append(f"Duration: {format_duration(duration)}")
        
        if headers:
            lines.append("Headers:")
            for key, value in headers.items():
                lines.append(f"  {key}: {value}")
        
        if body:
            body = truncate_body(body, self.config.max_body_length)
            lines.append(f"Body:\n{body}")
        
        lines.append("=" * 50)
        
        self._logger.debug("\n".join(lines))
    
    def log_error(self, message: str, exc_info: Optional[Exception] = None):
        """Log an error message."""
        if exc_info:
            self._logger.error(f"{message}: {exc_info}", exc_info=True)
        else:
            self._logger.error(message)
    
    def log_info(self, message: str):
        """Log an info message."""
        self._logger.info(message)
    
    def log_warning(self, message: str):
        """Log a warning message."""
        self._logger.warning(message)


# Global logger instance
_logger_instance: Optional[APIDebuggerLogger] = None


def get_logger(name: str = "api_debugger") -> APIDebuggerLogger:
    """
    Get or create a logger instance.
    
    Args:
        name: Logger name
    
    Returns:
        APIDebuggerLogger instance
    """
    global _logger_instance
    
    if _logger_instance is None:
        _logger_instance = APIDebuggerLogger(name)
    
    return _logger_instance


def reset_logger():
    """Reset the global logger instance."""
    global _logger_instance
    _logger_instance = None