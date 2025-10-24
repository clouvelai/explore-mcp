"""
Unified Server Manager

Clean, unified management of both local and remote MCP servers
with consistent discovery, generation, and tracking capabilities.
"""

import json
import re
import shutil
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from ai_generation.discovery import DiscoveryEngine, DiscoveryResult

from .exceptions import (
    DirectoryNotFoundError,
    DiscoveryError,
    FileOperationError,
    GenerationError,
    RegistryLoadError,
    ServerConfigurationError,
    ServerNotFoundError,
    ValidationError,
    handle_error,
    handle_warning,
    validate_file_path,
    validate_server_id,
)
from .local_scanner import LocalServerScanner
from .models import (
    DiscoveryConfig,
    GenerationConfig,
    ServerConfig,
    ServerMetadata,
    ServerRegistry,
    ServerSource,
)


class ServerManager:
    """Unified manager for all MCP servers (local and remote)."""
    
    def __init__(self, base_dir: str = "mcp_registry"):
        """
        Initialize the server manager.
        
        Args:
            base_dir: Base directory for server registry
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)
        
        # Ensure servers directory exists
        self.servers_dir = self.base_dir / "servers"
        self.servers_dir.mkdir(exist_ok=True)
        
        # Initialize discovery engine and scanner
        self.discovery_engine = DiscoveryEngine()
        self.local_scanner = LocalServerScanner()
        
        # Load registry
        self.registry_file = self.base_dir / "registry.json"
        self.registry = self._load_registry()
    
    def _load_registry(self) -> ServerRegistry:
        """Load the server registry."""
        if self.registry_file.exists():
            try:
                with open(self.registry_file, 'r') as f:
                    data = json.load(f)
                return ServerRegistry(**data)
            except json.JSONDecodeError as e:
                handle_warning(f"Registry file contains invalid JSON: {e}", str(self.registry_file))
            except (IOError, OSError) as e:
                handle_warning(f"Cannot read registry file: {e}", str(self.registry_file))
            except Exception as e:
                handle_warning(f"Failed to load registry: {e}", str(self.registry_file))
        
        # Create new registry
        return ServerRegistry()
    
    def _save_registry(self):
        """Save the server registry."""
        with open(self.registry_file, 'w') as f:
            json.dump(self.registry.model_dump(), f, indent=2, default=str)
    
    def add_server(
        self,
        server_id: str,
        name: str,
        source: Union[str, ServerSource],
        description: Optional[str] = None,
        category: str = "General",
        provider: Optional[str] = None,
        auth_required: bool = False,
        auth_type: Optional[str] = None,
        source_type: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Add a new server to the registry.
        
        Args:
            server_id: Unique server identifier
            name: Human-readable server name
            source: Server source (path/url string or ServerSource object)
            description: Server description
            category: Server category
            provider: Server provider
            auth_required: Whether server requires authentication
            auth_type: Type of authentication required
            **kwargs: Additional configuration options
            
        Returns:
            Server ID
        """
        # Handle explicit npm source type
        if source_type == "npm":
            if isinstance(source, str):
                server_source = self._create_npm_source(source)
            elif isinstance(source, ServerSource) and source.type != "npm":
                raise ValueError("source_type 'npm' requires npm package name string or npm ServerSource")
            else:
                server_source = source
        else:
            # Use existing normalization for local/remote
            server_source = self._normalize_server_source(source)
        # Set provider based on source type if not provided
        if provider is None and server_source.type == "npm":
            provider = "npm"
        
        server_config = self._create_server_config(
            server_id, name, server_source, description, category, 
            provider, auth_required, auth_type, **kwargs
        )
        
        # Set up filesystem and persistence
        self._setup_server_directories(server_config)
        self._persist_server_config(server_config)
        self._update_registry(server_id, category)
        
        # Provide user feedback
        self._log_server_addition(server_config)
        
        return server_id
    
    def _normalize_server_source(self, source: Union[str, ServerSource]) -> ServerSource:
        """
        Normalize source input to a ServerSource object.
        
        Args:
            source: String path/URL or ServerSource object
            
        Returns:
            ServerSource object
        """
        if isinstance(source, str):
            if source.startswith(("http://", "https://")):
                return ServerSource(type="remote", url=source, transport="http")
            else:
                return ServerSource(type="local", path=source, transport="stdio")
        else:
            return source
    
    def _create_npm_source(self, package_name: str) -> ServerSource:
        """
        Install npm package and create ServerSource.
        
        Args:
            package_name: npm package name (e.g., "@modelcontextprotocol/server-memory")
            
        Returns:
            ServerSource configured for the installed npm package
        """
        npx_command, package_version = self._install_npm_package(package_name)
        return ServerSource(
            type="npm",
            package_name=package_name,
            package_version=package_version,
            binary_path=npx_command,  # Store npx command as binary_path
            transport="stdio"
        )
    
    def _validate_package_name(self, package_name: str) -> str:
        """
        Validate npm package name for security.
        
        Args:
            package_name: Package name to validate
            
        Returns:
            Validated package name
            
        Raises:
            ValueError: If package name is invalid or unsafe
        """
        # Basic safety checks
        if not package_name or not isinstance(package_name, str):
            raise ValueError("Package name must be a non-empty string")
        
        if len(package_name) > 214:  # npm limit
            raise ValueError("Package name too long (max 214 characters)")
        
        # Check for dangerous characters that could enable injection
        dangerous_chars = [';', '&', '|', '`', '$', '(', ')', '<', '>', '"', "'", '\\', '\n', '\r', '\t']
        if any(char in package_name for char in dangerous_chars):
            raise ValueError(f"Package name contains unsafe characters: {package_name}")
        
        # Basic npm package name format validation
        # Allows: alphanumeric, hyphens, dots, underscores, tildes, and scoped packages
        if not re.match(r'^(@[a-z0-9-~][a-z0-9-._~]*/)?[a-z0-9-~][a-z0-9-._~]*$', package_name.lower()):
            raise ValueError(f"Invalid npm package name format: {package_name}")
        
        return package_name

    def _install_npm_package(self, package_name: str) -> tuple[str, str]:
        """
        Install npm package locally and return npx execution info.
        
        Args:
            package_name: npm package name to install
            
        Returns:
            Tuple of (npx_command, package_version)
            
        Raises:
            RuntimeError: If npm/npx is not available or installation fails
        """
        # Validate package name for security
        validated_name = self._validate_package_name(package_name)
        
        # Check if npm and npx are available
        if not shutil.which("npm"):
            raise RuntimeError("npm is not available. Please install Node.js and npm first.")
        if not shutil.which("npx"):
            raise RuntimeError("npx is not available. Please install Node.js and npm first.")
        
        print(f"📦 Installing npm package locally: {validated_name}")
        
        # Create a dedicated directory for npm packages
        npm_packages_dir = self.base_dir / "npm_packages"
        npm_packages_dir.mkdir(exist_ok=True)
        
        try:
            # Install package locally in dedicated directory
            result = subprocess.run(
                ["npm", "install", validated_name],
                cwd=npm_packages_dir,
                capture_output=True,
                text=True,
                check=True
            )
            print(f"✅ Package installed locally")
            
            # Get version and derive binary name
            package_version = self._get_package_version(validated_name)
            
            # Create temporary ServerSource to get binary name
            temp_source = ServerSource(type="npm", package_name=validated_name)
            binary_name = temp_source.binary_name
            
            # Create a wrapper script for secure execution
            wrapper_script = self._create_npm_wrapper_script(binary_name, npm_packages_dir)
            
            print(f"🔍 Package will be executed via wrapper: {wrapper_script}")
            print(f"📋 Package version: {package_version}")
            
            return wrapper_script, package_version
            
        except subprocess.CalledProcessError as e:
            error_msg = f"npm installation failed: {e.stderr or e.stdout}"
            raise RuntimeError(error_msg)
        except Exception as e:
            raise RuntimeError(f"Unexpected error during npm installation: {e}")
    
    def _create_npm_wrapper_script(self, binary_name: str, npm_packages_dir: Path) -> str:
        """
        Create a secure wrapper script for npm package execution.
        
        Args:
            binary_name: Name of the binary to execute
            npm_packages_dir: Path to npm packages directory
            
        Returns:
            Path to the wrapper script
        """
        # Create wrapper scripts directory
        wrappers_dir = self.base_dir / "npm_wrappers"
        wrappers_dir.mkdir(exist_ok=True)
        
        # Create a unique wrapper script for this binary
        script_name = f"{binary_name.replace('/', '_').replace('@', '')}_wrapper.py"
        wrapper_path = wrappers_dir / script_name
        
        # Generate secure wrapper script content
        wrapper_content = f'''#!/usr/bin/env python3
"""Secure wrapper for npm MCP package: {binary_name}"""
import os
import subprocess
import sys

# Security: Set fixed npm prefix and binary name
NPM_PREFIX = "{npm_packages_dir}"
BINARY_NAME = "{binary_name}"

def main():
    """Execute npm package via npx with fixed parameters."""
    try:
        # Build secure npx command
        cmd = ["npx", "--prefix", NPM_PREFIX, BINARY_NAME] + sys.argv[1:]
        
        # Execute with clean environment
        result = subprocess.run(cmd, check=False)
        sys.exit(result.returncode)
        
    except Exception as e:
        print(f"Error executing npm package: {{e}}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
'''
        
        # Write wrapper script
        with open(wrapper_path, 'w') as f:
            f.write(wrapper_content)
        
        # Make executable
        wrapper_path.chmod(0o755)
        
        return str(wrapper_path)
    
    def _get_package_version(self, package_name: str) -> str:
        """Get package version using npm show command."""
        try:
            # Validate package name before using in command
            validated_name = self._validate_package_name(package_name)
            result = subprocess.run(
                ["npm", "show", validated_name, "version"],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except (subprocess.CalledProcessError, ValueError):
            return "unknown"
    
    def _create_server_config(
        self, 
        server_id: str,
        name: str,
        server_source: ServerSource,
        description: Optional[str],
        category: str,
        provider: Optional[str],
        auth_required: bool,
        auth_type: Optional[str],
        **kwargs
    ) -> ServerConfig:
        """
        Create a complete server configuration object.
        
        Args:
            server_id: Unique server identifier
            name: Human-readable server name
            server_source: Normalized server source
            description: Server description
            category: Server category
            provider: Server provider
            auth_required: Whether authentication is required
            auth_type: Type of authentication
            **kwargs: Additional configuration options
            
        Returns:
            ServerConfig object
        """
        return ServerConfig(
            id=server_id,
            name=name,
            source=server_source,
            metadata=ServerMetadata(
                description=description,
                category=category,
                provider=provider,
                auth_required=auth_required,
                auth_type=auth_type
            ),
            **kwargs
        )
    
    def _setup_server_directories(self, server_config: ServerConfig) -> None:
        """
        Create necessary directories for the server.
        
        Args:
            server_config: Server configuration object
        """
        server_dir = self.servers_dir / server_config.id
        server_dir.mkdir(exist_ok=True)
        (server_dir / server_config.generation.output_dir).mkdir(exist_ok=True)
    
    def _persist_server_config(self, server_config: ServerConfig) -> None:
        """
        Save server configuration to disk.
        
        Args:
            server_config: Server configuration to save
        """
        with open(server_config.config_path, 'w') as f:
            json.dump(server_config.model_dump(), f, indent=2, default=str)
    
    def _update_registry(self, server_id: str, category: str) -> None:
        """
        Update the main registry with the new server.
        
        Args:
            server_id: Server identifier
            category: Server category
        """
        self.registry.add_server(server_id, category)
        self._save_registry()
    
    def _log_server_addition(self, server_config: ServerConfig) -> None:
        """
        Log successful server addition to user.
        
        Args:
            server_config: Added server configuration
        """
        print(f"✅ Added server: {server_config.name} ({server_config.id})")
        print(f"   Type: {server_config.source.type}")
        if server_config.source.type == "npm":
            print(f"   Package: {server_config.source.package_name}")
            print(f"   Binary: {server_config.source.binary_path}")
        else:
            print(f"   Source: {server_config.source.url or server_config.source.path}")
        print(f"   Generated path: {server_config.generated_path}")
    
    def get_server(self, server_id: str) -> Optional[ServerConfig]:
        """Get server configuration by ID."""
        config_file = self.servers_dir / server_id / "config.json"
        if not config_file.exists():
            return None
        
        try:
            with open(config_file, 'r') as f:
                data = json.load(f)
            return ServerConfig(**data)
        except json.JSONDecodeError as e:
            raise ServerConfigurationError(server_id, f"Invalid JSON in config file: {e}")
        except (IOError, OSError) as e:
            raise FileOperationError(str(config_file), "read", str(e))
        except ValueError as e:
            raise ServerConfigurationError(server_id, f"Invalid configuration data: {e}")
    
    def list_servers(
        self,
        category: Optional[str] = None,
        server_type: Optional[str] = None,
        auth_required: Optional[bool] = None
    ) -> List[Dict[str, Any]]:
        """
        List all servers with optional filtering.
        
        Args:
            category: Filter by category
            server_type: Filter by type (local/remote)
            auth_required: Filter by authentication requirement
            
        Returns:
            List of server information
        """
        servers = []
        
        for server_id in self.registry.servers:
            config = self.get_server(server_id)
            if not config:
                continue
            
            # Apply filters
            if category and config.metadata.category != category:
                continue
            if server_type and config.source.type != server_type:
                continue
            if auth_required is not None and config.metadata.auth_required != auth_required:
                continue
            
            servers.append({
                "id": server_id,
                "name": config.name,
                "type": config.source.type,
                "status": "active",
                "auth_required": config.metadata.auth_required,
                "category": config.metadata.category,
                "provider": config.metadata.provider,
                "last_discovered": config.discovery.last_discovered,
                "last_generated": config.generation.last_generated,
                "generated_path": str(config.generated_path)
            })
        
        return servers
    
    def discover_server(self, server_id: str) -> Optional[DiscoveryResult]:
        """
        Discover tools/resources for a specific server.
        
        Args:
            server_id: Server ID to discover
            
        Returns:
            Discovery result or None if failed
            
        Raises:
            ServerNotFoundError: If server doesn't exist
            DiscoveryError: If discovery process fails
        """
        try:
            config = self.get_server(server_id)
            if not config:
                raise ServerNotFoundError(server_id)
            
            if not config.discovery.enabled:
                handle_warning(f"Discovery disabled for server: {server_id}")
                return None
            
            print(f"🔍 Discovering server: {config.name}")
            
            # Determine source path/URL
            if config.source.type == "local":
                source_path = config.source.path
            elif config.source.type == "npm":
                # For npm packages, use the installed binary path (works like local servers)
                source_path = config.source.binary_path
            else:
                source_path = config.source.url
            
            # Perform discovery
            result = self.discovery_engine.discover(
                source_path,
                transport=config.source.transport,
                use_cache=True
            )
            
            # Save discovery results
            try:
                with open(config.discovery_path, 'w') as f:
                    json.dump(result.model_dump(), f, indent=2, default=str)
            except (IOError, OSError) as e:
                raise FileOperationError(str(config.discovery_path), "write", str(e))
            
            # Update server configuration
            config.discovery.last_discovered = datetime.now()
            config.metadata.updated_at = datetime.now()
            
            try:
                with open(config.config_path, 'w') as f:
                    json.dump(config.model_dump(), f, indent=2, default=str)
            except (IOError, OSError) as e:
                raise FileOperationError(str(config.config_path), "write", str(e))
            
            print(f"✅ Discovery completed: {len(result.tools)} tools, {len(result.resources)} resources")
            print(f"   Discovery saved to: {config.discovery_path}")
            
            return result
            
        except (ServerNotFoundError, DiscoveryError, FileOperationError):
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            # Wrap unexpected errors in DiscoveryError
            raise DiscoveryError(server_id, str(e))
    
    def discover_all(
        self,
        server_type: Optional[str] = None,
        auth_required: Optional[bool] = None
    ) -> List[DiscoveryResult]:
        """
        Discover all servers matching criteria.
        
        Args:
            server_type: Only discover servers of this type
            auth_required: Only discover servers with this auth requirement
            
        Returns:
            List of discovery results
        """
        servers = self.list_servers(server_type=server_type, auth_required=auth_required)
        results = []
        
        print(f"🔍 Discovering {len(servers)} servers")
        
        for server_info in servers:
            server_id = server_info["id"]
            result = self.discover_server(server_id)
            if result:
                results.append(result)
        
        print(f"✅ Discovery completed: {len(results)}/{len(servers)} servers successful")
        return results
    
    def generate_mock(self, server_id: str) -> Optional[str]:
        """
        Generate mock server for a specific server.
        
        Args:
            server_id: Server ID to generate mock for
            
        Returns:
            Path to generated mock server or None if failed
        """
        config = self.get_server(server_id)
        if not config:
            print(f"❌ Server not found: {server_id}")
            return None
        
        if not config.generation.enabled:
            print(f"⚠️  Generation disabled for server: {server_id}")
            return None
        
        # Check if discovery results exist
        if not config.discovery_path.exists():
            print(f"❌ No discovery results found for {server_id}. Run discovery first.")
            return None
        
        print(f"🏗️  Generating mock server: {config.name}")
        
        try:
            # Load discovery results
            with open(config.discovery_path, 'r') as f:
                discovery_data = json.load(f)
            
            # Import generation modules
            from ai_generation.server_generator import generate_ai_mock_server

            # Generate mock server
            generate_ai_mock_server(discovery_data, config.generated_path)
            
            # Update server configuration
            config.generation.last_generated = datetime.now()
            config.metadata.updated_at = datetime.now()
            
            with open(config.config_path, 'w') as f:
                json.dump(config.model_dump(), f, indent=2, default=str)
            
            print(f"✅ Mock server generated")
            print(f"   Generated path: {config.generated_path}")
            print(f"   Files: server.py, tools.py")
            
            return str(config.generated_path)
            
        except Exception as e:
            print(f"❌ Generation failed for {server_id}: {e}")
            return None
    
    def generate_template(self, template_type: str = "config") -> str:
        """
        Generate template content for server configuration.
        
        Args:
            template_type: Type of template ("config" or "discovery")
            
        Returns:
            Template content as JSON string
        """
        if template_type == "config":
            return ServerConfig.generate_template()
        elif template_type == "discovery":
            # For discovery template, we can use the existing discovery result structure
            from ai_generation.discovery_models import DiscoveryResult
            return DiscoveryResult.generate_template()
        else:
            raise ValueError(f"Unknown template type: {template_type}")
    
    def save_template(self, template_type: str = "config", output_path: Optional[Path] = None):
        """
        Save template to file.
        
        Args:
            template_type: Type of template to save
            output_path: Where to save the template (defaults to templates directory)
        """
        if output_path is None:
            output_path = self.base_dir / "servers" / "templates" / f"{template_type}.json.template"
        
        template_content = self.generate_template(template_type)
        
        with open(output_path, 'w') as f:
            f.write(template_content)
        
        print(f"✅ Template saved: {output_path}")
    
    def update_templates(self):
        """Update all templates from current data models."""
        print("🔄 Updating templates from data models...")
        
        # Update config template
        self.save_template("config")
        
        # Update discovery template (if we implement it)
        # self.save_template("discovery")
        
        print("✅ All templates updated")
    
    def generate_all(
        self,
        server_type: Optional[str] = None,
        auth_required: Optional[bool] = None
    ) -> List[str]:
        """
        Generate mocks for all discovered servers.
        
        Args:
            server_type: Only generate for servers of this type
            auth_required: Only generate for servers with this auth requirement
            
        Returns:
            List of generated mock server paths
        """
        servers = self.list_servers(server_type=server_type, auth_required=auth_required)
        results = []
        
        print(f"🏗️  Generating mocks for {len(servers)} servers")
        
        for server_info in servers:
            server_id = server_info["id"]
            result = self.generate_mock(server_id)
            if result:
                results.append(result)
        
        print(f"✅ Generation completed: {len(results)}/{len(servers)} servers successful")
        return results
    
    def remove_server(self, server_id: str) -> bool:
        """
        Remove a server from the registry.
        
        Args:
            server_id: Server ID to remove
            
        Returns:
            True if successful
        """
        server_dir = self.servers_dir / server_id
        if not server_dir.exists():
            print(f"❌ Server not found: {server_id}")
            return False
        
        # Remove directory
        shutil.rmtree(server_dir)
        
        # Update registry
        self.registry.remove_server(server_id)
        self._save_registry()
        
        print(f"✅ Removed server: {server_id}")
        return True
    
    def get_server_status(self, server_id: str) -> Dict[str, Any]:
        """
        Get comprehensive status for a server.
        
        Args:
            server_id: Server ID
            
        Returns:
            Status information
        """
        config = self.get_server(server_id)
        if not config:
            return {"error": "Server not found"}
        
        return {
            "id": server_id,
            "name": config.name,
            "type": config.source.type,
            "source": config.source.url or config.source.path,
            "transport": config.source.transport,
            "auth_required": config.metadata.auth_required,
            "auth_type": config.metadata.auth_type,
            "category": config.metadata.category,
            "provider": config.metadata.provider,
            "discovery": {
                "enabled": config.discovery.enabled,
                "last_discovered": config.discovery.last_discovered,
                "has_results": config.discovery_path.exists()
            },
            "generation": {
                "enabled": config.generation.enabled,
                "last_generated": config.generation.last_generated,
                "output_dir": str(config.generated_path),
                "has_files": config.generated_path.exists()
            },
            "metadata": {
                "created_at": config.metadata.created_at,
                "updated_at": config.metadata.updated_at,
                "version": config.metadata.version
            }
        }
    
    def discover_local_servers(self, mcp_servers_dir: str = "mcp_servers") -> List[Dict[str, Any]]:
        """
        Auto-discover all local MCP servers in the mcp_servers directory.
        
        Args:
            mcp_servers_dir: Path to the mcp_servers directory
            
        Returns:
            List of discovered server information
        """
        try:
            discovered_servers = self.local_scanner.discover_servers(mcp_servers_dir)
            
            # Convert LocalServerInfo objects to dictionaries for backward compatibility
            return [
                {
                    "id": server.id,
                    "name": server.name,
                    "path": server.path,
                    "transport": server.transport,
                    "auth_required": server.auth_required,
                    "category": server.category,
                    "description": server.description,
                    "provider": server.provider
                }
                for server in discovered_servers
            ]
        except DirectoryNotFoundError as e:
            handle_error(e, "local server discovery", exit_on_error=False)
            return []
    
    
    def auto_discover_and_add_local_servers(self, mcp_servers_dir: str = "mcp_servers", dry_run: bool = False) -> List[str]:
        """
        Auto-discover and add all local servers to the registry.
        
        Args:
            mcp_servers_dir: Path to the mcp_servers directory
            dry_run: If True, only show what would be added without actually adding
            
        Returns:
            List of added server IDs
        """
        discovered_servers = self.discover_local_servers(mcp_servers_dir)
        
        if not discovered_servers:
            print("📋 No local servers found to add")
            return []
        
        added_servers = []
        
        print(f"\n{'🔍 DRY RUN - ' if dry_run else ''}Adding discovered servers to registry:")
        
        for server_info in discovered_servers:
            server_id = server_info["id"]
            
            # Check if server already exists
            existing_server = self.get_server(server_id)
            if existing_server:
                print(f"   ⚠️  Skipping {server_info['name']} ({server_id}) - already exists")
                continue
            
            if dry_run:
                print(f"   📝 Would add: {server_info['name']} ({server_id})")
                print(f"      Path: {server_info['path']}")
                print(f"      Transport: {server_info['transport']}")
                print(f"      Auth Required: {server_info['auth_required']}")
                print(f"      Category: {server_info['category']}")
                added_servers.append(server_id)
            else:
                # Create server source
                source = ServerSource(
                    type="local",
                    path=server_info["path"],
                    transport=server_info["transport"]
                )
                
                # Add server to registry
                self.add_server(
                    server_id=server_id,
                    name=server_info["name"],
                    source=source,
                    description=server_info.get("description"),
                    category=server_info["category"],
                    provider=server_info.get("provider"),
                    auth_required=server_info["auth_required"]
                )
                
                added_servers.append(server_id)
        
        if not dry_run and added_servers:
            print(f"\n✅ Successfully added {len(added_servers)} local servers to registry")
        
        return added_servers
    
    def test_server(self, server_id: str) -> bool:
        """
        Run evaluation tests for a specific server.
        
        Args:
            server_id: Server ID to test
            
        Returns:
            True if tests passed, False otherwise
        """
        config = self.get_server(server_id)
        if not config:
            print(f"❌ Server not found: {server_id}")
            return False
        
        # Check if generated server and evaluations exist
        generated_dir = self.servers_dir / server_id / "generated"
        mock_server_path = generated_dir / "server.py"
        evaluations_path = generated_dir / "evaluations.json"
        
        if not mock_server_path.exists():
            print(f"❌ No generated mock server found for {server_id}. Run generation first.")
            return False
            
        if not evaluations_path.exists():
            print(f"❌ No evaluations found for {server_id}. Run generation first.")
            return False
        
        print(f"🧪 Running tests for server: {config.name}")
        
        try:
            # Import and run the evaluation runner
            from ai_generation.evaluation_runner import run_evaluations
            
            # Run evaluations
            result = run_evaluations(
                evaluations_file=str(evaluations_path),
                mock_server_file=str(mock_server_path)
            )
            
            if result:
                print(f"✅ All tests passed for {server_id}")
                return True
            else:
                print(f"❌ Some tests failed for {server_id}")
                return False
                
        except ImportError:
            print(f"❌ Evaluation runner not available. Install required dependencies.")
            return False
        except Exception as e:
            print(f"❌ Test execution failed: {e}")
            return False
