"""
Custom exception types for MCP Registry operations.

Provides structured error handling with specific exception types for different
failure scenarios, improving debugging and error reporting.
"""

import sys
from typing import Optional


class MCPRegistryError(Exception):
    """Base exception for all MCP Registry operations."""
    
    def __init__(self, message: str, context: Optional[str] = None, exit_code: int = 1):
        """
        Initialize MCP Registry error.
        
        Args:
            message: Human-readable error message
            context: Additional context (e.g., server_id, file_path)
            exit_code: Exit code for CLI operations (1 for general errors)
        """
        super().__init__(message)
        self.message = message
        self.context = context
        self.exit_code = exit_code
    
    def __str__(self) -> str:
        """Return formatted error message."""
        if self.context:
            return f"{self.message} (context: {self.context})"
        return self.message


class ServerNotFoundError(MCPRegistryError):
    """Raised when a server is not found in the registry."""
    
    def __init__(self, server_id: str):
        super().__init__(
            message=f"Server not found: {server_id}",
            context=f"server_id={server_id}",
            exit_code=1
        )
        self.server_id = server_id


class ServerConfigurationError(MCPRegistryError):
    """Raised when server configuration is invalid or corrupted."""
    
    def __init__(self, server_id: str, reason: str):
        super().__init__(
            message=f"Server configuration error: {reason}",
            context=f"server_id={server_id}",
            exit_code=1
        )
        self.server_id = server_id
        self.reason = reason


class RegistryLoadError(MCPRegistryError):
    """Raised when registry file cannot be loaded."""
    
    def __init__(self, registry_path: str, reason: str):
        super().__init__(
            message=f"Failed to load registry: {reason}",
            context=f"registry_path={registry_path}",
            exit_code=1
        )
        self.registry_path = registry_path
        self.reason = reason


class DiscoveryError(MCPRegistryError):
    """Raised when server discovery fails."""
    
    def __init__(self, server_id: str, reason: str):
        super().__init__(
            message=f"Discovery failed: {reason}",
            context=f"server_id={server_id}",
            exit_code=1
        )
        self.server_id = server_id
        self.reason = reason


class GenerationError(MCPRegistryError):
    """Raised when mock server generation fails."""
    
    def __init__(self, server_id: str, reason: str):
        super().__init__(
            message=f"Generation failed: {reason}",
            context=f"server_id={server_id}",
            exit_code=1
        )
        self.server_id = server_id
        self.reason = reason


class DirectoryNotFoundError(MCPRegistryError):
    """Raised when required directory is not found."""
    
    def __init__(self, directory_path: str):
        super().__init__(
            message=f"Directory not found: {directory_path}",
            context=f"directory_path={directory_path}",
            exit_code=1
        )
        self.directory_path = directory_path


class FileOperationError(MCPRegistryError):
    """Raised when file operations fail."""
    
    def __init__(self, file_path: str, operation: str, reason: str):
        super().__init__(
            message=f"File {operation} failed: {reason}",
            context=f"file_path={file_path}",
            exit_code=1
        )
        self.file_path = file_path
        self.operation = operation
        self.reason = reason


class ValidationError(MCPRegistryError):
    """Raised when input validation fails."""
    
    def __init__(self, field: str, value: str, reason: str):
        super().__init__(
            message=f"Validation failed for {field}: {reason}",
            context=f"field={field}, value={value}",
            exit_code=1
        )
        self.field = field
        self.value = value
        self.reason = reason


def handle_error(error: Exception, context: str = "", exit_on_error: bool = False) -> None:
    """
    Standardized error handler for consistent error reporting.
    
    Args:
        error: Exception that occurred
        context: Additional context for the error
        exit_on_error: Whether to exit the program after handling
    """
    if isinstance(error, MCPRegistryError):
        # Custom error - use structured message
        print(f"❌ {error.message}")
        if error.context and context:
            print(f"   Context: {context}")
        elif error.context:
            print(f"   Context: {error.context}")
        elif context:
            print(f"   Context: {context}")
        
        if exit_on_error:
            sys.exit(error.exit_code)
    
    else:
        # Generic error - provide more context
        print(f"❌ Unexpected error in {context}: {error}")
        print("   This may indicate a bug or system issue.")
        print("   Please check your configuration and try again.")
        
        if exit_on_error:
            # For debugging, show full traceback for unexpected errors
            import traceback
            traceback.print_exc()
            sys.exit(2)  # Different exit code for unexpected errors


def handle_warning(message: str, context: str = "") -> None:
    """
    Standardized warning handler.
    
    Args:
        message: Warning message
        context: Additional context
    """
    print(f"⚠️  Warning: {message}")
    if context:
        print(f"   Context: {context}")


def validate_server_id(server_id: str) -> None:
    """
    Validate server ID format.
    
    Args:
        server_id: Server identifier to validate
        
    Raises:
        ValidationError: If server ID is invalid
    """
    if not server_id:
        raise ValidationError("server_id", server_id, "Server ID cannot be empty")
    
    if not server_id.replace('-', '').replace('_', '').isalnum():
        raise ValidationError(
            "server_id", 
            server_id, 
            "Server ID must contain only alphanumeric characters, hyphens, and underscores"
        )
    
    if len(server_id) > 50:
        raise ValidationError("server_id", server_id, "Server ID must be 50 characters or less")


def validate_file_path(file_path: str, must_exist: bool = False) -> None:
    """
    Validate file path format and existence.
    
    Args:
        file_path: File path to validate
        must_exist: Whether the file must already exist
        
    Raises:
        ValidationError: If file path is invalid
        FileOperationError: If file doesn't exist when required
    """
    if not file_path:
        raise ValidationError("file_path", file_path, "File path cannot be empty")
    
    if must_exist:
        from pathlib import Path
        if not Path(file_path).exists():
            raise FileOperationError(file_path, "read", "File does not exist")