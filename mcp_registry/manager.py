"""
Unified Server Manager

Clean, unified management of both local and remote MCP servers
with consistent discovery, generation, and tracking capabilities.
"""

import json
import shutil
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from .models import ServerConfig, ServerRegistry, ServerSource, DiscoveryConfig, GenerationConfig, ServerMetadata
from .exceptions import (
    ServerNotFoundError, ServerConfigurationError, RegistryLoadError, 
    DiscoveryError, GenerationError, DirectoryNotFoundError, FileOperationError,
    ValidationError, handle_error, handle_warning, validate_server_id, validate_file_path
)
from ai_generation.discovery import DiscoveryEngine, DiscoveryResult


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
        
        # Initialize discovery engine
        self.discovery_engine = DiscoveryEngine()
        
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
        # Normalize and create server configuration
        server_source = self._normalize_server_source(source)
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
        servers_dir = Path(mcp_servers_dir)
        if not servers_dir.exists():
            print(f"❌ MCP servers directory not found: {mcp_servers_dir}")
            return []
        
        discovered_servers = []
        
        print(f"🔍 Scanning {mcp_servers_dir} for MCP servers...")
        
        # Look for server.py files in subdirectories
        for server_dir in servers_dir.iterdir():
            if not server_dir.is_dir():
                continue
            
            server_file = server_dir / "server.py"
            if not server_file.exists():
                continue
            
            # Extract server metadata from the server file
            server_info = self._extract_server_metadata(server_file)
            
            # Generate server ID from directory name
            server_id = server_dir.name
            
            # Determine transport type from server file
            transport = self._detect_transport_type(server_file)
            
            # Check if server requires authentication
            auth_required = self._detect_auth_requirement(server_file)
            
            server_info.update({
                "id": server_id,
                "path": str(server_file),
                "transport": transport,
                "auth_required": auth_required,
                "category": self._categorize_server(server_info.get("name", server_id))
            })
            
            discovered_servers.append(server_info)
            print(f"   ✅ Found: {server_info['name']} ({server_id})")
        
        print(f"🎯 Discovered {len(discovered_servers)} local servers")
        return discovered_servers
    
    def _extract_server_metadata(self, server_file: Path) -> Dict[str, Any]:
        """
        Extract metadata from a server.py file.
        
        Args:
            server_file: Path to the server.py file
            
        Returns:
            Dictionary with extracted metadata
        """
        try:
            with open(server_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract server name from FastMCP constructor
            name_match = re.search(r'FastMCP\("([^"]+)"\)', content)
            server_name = name_match.group(1) if name_match else server_file.parent.name.title()
            
            # Extract description from docstring
            desc_match = re.search(r'"""(.*?)"""', content, re.DOTALL)
            description = None
            if desc_match:
                desc_text = desc_match.group(1).strip()
                # Take first line as description
                description = desc_text.split('\n')[0].strip()
            
            # Extract provider from imports or comments
            provider = None
            if "gmail" in content.lower():
                provider = "Google"
            elif "google" in content.lower():
                provider = "Google"
            elif "microsoft" in content.lower():
                provider = "Microsoft"
            
            return {
                "name": server_name,
                "description": description,
                "provider": provider
            }
            
        except Exception as e:
            print(f"⚠️  Warning: Could not extract metadata from {server_file}: {e}")
            return {
                "name": server_file.parent.name.title(),
                "description": None,
                "provider": None
            }
    
    def _detect_transport_type(self, server_file: Path) -> str:
        """
        Detect the transport type used by a server.
        
        Args:
            server_file: Path to the server.py file
            
        Returns:
            Transport type (stdio, sse, http)
        """
        try:
            with open(server_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for SSE/HTTP transport
            if 'transport="sse"' in content or 'transport="http"' in content:
                return "sse"
            elif 'mcp.run(transport="sse"' in content:
                return "sse"
            elif 'mcp.run(transport="http"' in content:
                return "http"
            
            # Default to stdio
            return "stdio"
            
        except Exception:
            return "stdio"
    
    def _detect_auth_requirement(self, server_file: Path) -> bool:
        """
        Detect if a server requires authentication.
        
        Args:
            server_file: Path to the server.py file
            
        Returns:
            True if authentication is required
        """
        try:
            with open(server_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Look for authentication-related keywords
            auth_keywords = [
                "oauth", "authentication", "auth", "credentials", 
                "api_key", "token", "login", "environment variables"
            ]
            
            content_lower = content.lower()
            return any(keyword in content_lower for keyword in auth_keywords)
            
        except Exception:
            return False
    
    def _categorize_server(self, server_name: str) -> str:
        """
        Categorize a server based on its name.
        
        Args:
            server_name: Name of the server
            
        Returns:
            Category string
        """
        name_lower = server_name.lower()
        
        if any(word in name_lower for word in ["gmail", "email", "mail"]):
            return "Communication"
        elif any(word in name_lower for word in ["drive", "storage", "file"]):
            return "Storage"
        elif any(word in name_lower for word in ["calculator", "math", "compute"]):
            return "Utilities"
        elif any(word in name_lower for word in ["air", "fryer", "cooking", "recipe"]):
            return "Lifestyle"
        elif any(word in name_lower for word in ["git", "github", "repository"]):
            return "Development"
        elif any(word in name_lower for word in ["docs", "documentation", "learn"]):
            return "Documentation"
        else:
            return "General"
    
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
