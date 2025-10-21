#!/usr/bin/env python3
"""
MCP Discovery Engine - Uses MCP Inspector CLI for comprehensive server discovery.

This module provides a streamlined discovery mechanism that leverages the official
MCP Inspector tool to discover tools, resources, prompts, and server metadata.

Key Features:
- Unified discovery using MCP Inspector CLI (npx @modelcontextprotocol/inspector)
- Support for all transport types (stdio, http, sse) with auto-detection
- Intelligent caching with configurable TTL (default: 15 minutes)
- Comprehensive error handling and dependency checking
- Support for Python, Node.js, and TypeScript MCP servers

Usage:
    from ai_generation.discovery import DiscoveryEngine
    
    # Basic usage (no caching)
    engine = DiscoveryEngine()
    result = engine.discover('path/to/server.py')
    
    # With caching enabled
    result = engine.discover('path/to/server.py', use_cache=True)
    
    # Custom cache settings
    engine = DiscoveryEngine(cache_dir='/tmp/custom-cache')
    engine.cache_ttl = 300  # 5 minutes
    result = engine.discover('path/to/server.py', use_cache=True)

Dependencies:
- Node.js and npx (for MCP Inspector)
- @modelcontextprotocol/inspector package (installed automatically via npx)

Output Format:
    {
        "server_path": "path/to/server.py",
        "transport": "stdio",
        "command": "uv run python path/to/server.py",
        "tools": [{"name": "...", "description": "...", "inputSchema": {...}}],
        "resources": [{"uri": "...", "name": "...", "mimeType": "..."}],
        "prompts": [{"name": "...", "description": "...", "arguments": [...]}],
        "server_info": {"name": "...", "version": "..."},
        "metadata": {
            "discovered_at": "2024-10-21T...",
            "discovery_method": "mcp-inspector",
            "cache_hit": false,
            "discovery_time_ms": 4500
        }
    }
"""

import json
import subprocess
import hashlib
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Literal
from datetime import datetime
try:
    from .discovery_models import DiscoveryResult, DiscoveryMetadata, MCPTool, MCPResource, MCPPrompt, ServerInfo
except ImportError:
    # For direct execution
    from discovery_models import DiscoveryResult, DiscoveryMetadata, MCPTool, MCPResource, MCPPrompt, ServerInfo

# Type aliases for better type safety
TransportType = Literal["auto", "stdio", "sse", "http"]

# Transport type constants
class Transport:
    AUTO = "auto"
    STDIO = "stdio"
    SSE = "sse" 
    HTTP = "http"


class DependencyError(Exception):
    """Raised when required dependencies are not available."""
    pass


class DiscoveryError(Exception):
    """Raised when discovery fails."""
    pass


class DiscoveryEngine:
    """
    MCP server discovery using MCP Inspector CLI.
    
    This engine uses the official MCP Inspector tool to discover server capabilities,
    including tools, resources, prompts, and metadata. It includes caching to improve
    performance for repeated discoveries.
    
    Attributes:
        cache_dir (Path): Directory for storing cache files
        cache_ttl (int): Cache time-to-live in seconds (default: 900 = 15 minutes)
    
    Examples:
        # Basic discovery without caching
        engine = DiscoveryEngine()
        data = engine.discover('mcp_servers/calculator/server.py')
        
        # Discovery with caching enabled
        data = engine.discover('mcp_servers/calculator/server.py', use_cache=True)
        
        # Custom transport type
        data = engine.discover('server.py', transport='http')
        
        # Clear all cached data
        engine.clear_cache()
    """
    
    def __init__(self, cache_dir: str = ".mcp-ci/cache"):
        """
        Initialize the discovery engine.
        
        Args:
            cache_dir (str): Directory for caching discovery results. Will be created
                           if it doesn't exist. Defaults to '.mcp-ci/cache'.
        
        Note:
            The cache directory structure will be:
            cache_dir/
            ├── abc123def.json  # MD5 hash of server path
            ├── def456ghi.json
            └── ...
        """
        self.cache_dir = Path(cache_dir)
        self.cache_ttl = 900  # 15 minutes in seconds
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
    def check_dependencies(self) -> bool:
        """
        Check if required dependencies are available.
        
        Returns:
            True if all dependencies are available
            
        Raises:
            DependencyError: If npx is not available
        """
        try:
            result = subprocess.run(
                ["npx", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode != 0:
                raise DependencyError(
                    "npx not found. Install Node.js and npm, then npx will be available."
                )
            return True
        except FileNotFoundError:
            raise DependencyError(
                "npx not found. Install Node.js and npm from https://nodejs.org/"
            )
        except subprocess.TimeoutExpired:
            raise DependencyError("npx check timed out")
    
    def discover(
        self, 
        server_path: str, 
        transport: TransportType = Transport.AUTO,
        use_cache: bool = False  # TODO: Enable by default in CI/production after prototyping phase
    ) -> DiscoveryResult:
        """
        Discover MCP server capabilities using Inspector CLI.
        
        This is the main entry point for server discovery. It will:
        1. Check that npx and MCP Inspector are available
        2. Check cache for existing results (if use_cache=True)
        3. Auto-detect transport type if transport="auto"
        4. Execute MCP Inspector CLI to discover tools, resources, prompts
        5. Cache results for future use (if use_cache=True)
        
        Args:
            server_path (str): Path to the MCP server file. Can be:
                - Python files: 'server.py', 'mcp_servers/calculator/server.py'
                - Node.js files: 'server.js', 'server.mjs'
                - TypeScript files: 'server.ts'
                - Executable files: './server'
            transport (str): Transport type. Options:
                - "auto": Auto-detect based on server characteristics (default)
                - "stdio": Standard input/output transport
                - "http": HTTP transport
                - "sse": Server-sent events transport
            use_cache (bool): Whether to use cached results if available.
                - False: Always perform fresh discovery (default for development)
                - True: Use cache if available and not expired (recommended for CI)
            
        Returns:
            DiscoveryResult: Structured discovery results containing:
                - server_path: Original server path
                - transport: Detected/specified transport type
                - command: Actual command used to launch server
                - tools: List of discovered tools with schemas
                - resources: List of discovered resources
                - prompts: List of discovered prompts
                - server_info: Server metadata (if available)
                - metadata: Discovery metadata (timing, cache info, etc.)
            
        Raises:
            DependencyError: If npx or Node.js is not installed
            DiscoveryError: If server file not found or discovery fails
            
        Examples:
            # Basic discovery
            result = engine.discover('mcp_servers/calculator/server.py')
            print(f"Found {len(result['tools'])} tools")
            
            # With caching for faster repeated runs
            result = engine.discover('server.py', use_cache=True)
            
            # Force specific transport
            result = engine.discover('server.py', transport='http')
        """
        # Check dependencies first
        self.check_dependencies()
        
        # Validate server path or URL
        if server_path.startswith(("http://", "https://")):
            # For HTTP URLs, no local file validation needed
            print(f"🌐 HTTP server URL detected: {server_path}")
        else:
            # For local files, check existence
            server_file = Path(server_path)
            if not server_file.exists():
                raise DiscoveryError(f"Server file not found: {server_path}")
        
        # Check cache if enabled
        if use_cache:
            cached = self._get_cached_discovery(server_path)
            if cached:
                age_seconds = cached.metadata.cache_age_seconds or 0
                print(f"📦 Using cached discovery")
                print(f"   Cache age: {age_seconds}s / {self.cache_ttl}s TTL")
                print(f"   Cache location: {self.cache_dir}")
                return cached
        
        # Detect transport if auto
        if transport == Transport.AUTO:
            transport = self._detect_transport(server_path)
            print(f"🔍 Auto-detected transport: {transport}")
        
        # Build command based on server type
        server_cmd = self._build_command(server_path, transport)
        
        print(f"🔍 Discovering MCP server: {server_path}")
        print(f"   Transport: {transport}")
        print(f"   Command: {' '.join(server_cmd)}")
        
        start_time = time.time()
        
        # Initialize discovery data with structured models
        start_time_dt = datetime.now()
        tools = []
        resources = []
        prompts = []
        server_info = ServerInfo()
        
        # Create metadata object
        metadata = DiscoveryMetadata(
            discovered_at=start_time_dt,
            discovery_method="mcp-inspector",
            cache_hit=False
        )
        
        # Discover tools
        try:
            tools_result = self._execute_inspector(server_cmd, "tools/list")
            raw_tools = tools_result.get("tools", [])
            tools = [MCPTool(**tool) for tool in raw_tools]
            print(f"   ✓ Found {len(tools)} tools")
        except Exception as e:
            print(f"   ⚠️  Failed to discover tools: {e}")
        
        # Discover resources
        # Note: Currently only discovers static resources. Template resources (with parameters
        # like "resource://{param}") are not returned by MCP Inspector's resources/list method.
        # This is a known limitation that affects discovery but not runtime functionality.
        try:
            resources_result = self._execute_inspector(server_cmd, "resources/list")
            raw_resources = resources_result.get("resources", [])
            resources = [MCPResource(**resource) for resource in raw_resources]
            print(f"   ✓ Found {len(resources)} resources")
        except Exception as e:
            print(f"   ⚠️  Failed to discover resources: {e}")
        
        # Discover prompts
        try:
            prompts_result = self._execute_inspector(server_cmd, "prompts/list")
            raw_prompts = prompts_result.get("prompts", [])
            prompts = [MCPPrompt(**prompt) for prompt in raw_prompts]
            print(f"   ✓ Found {len(prompts)} prompts")
        except Exception as e:
            print(f"   ⚠️  Failed to discover prompts: {e}")
        
        # Try to get server info (may not be available)
        try:
            server_info_result = self._execute_inspector(server_cmd, "server/info")
            if server_info_result:
                server_info = ServerInfo(**server_info_result)
        except:
            pass  # Server info is optional
        
        # Add timing metadata
        discovery_time = time.time() - start_time
        metadata.discovery_time_ms = int(discovery_time * 1000)
        
        # Create the structured result
        discovery_result = DiscoveryResult(
            server_path=str(server_path),
            transport=transport,
            command=" ".join(server_cmd),
            tools=tools,
            resources=resources,
            prompts=prompts,
            server_info=server_info,
            metadata=metadata
        )
        
        # Cache the results (convert to dict for storage)
        if use_cache:
            self._cache_discovery(server_path, discovery_result.model_dump())
        
        print(f"✅ Discovery completed in {discovery_time:.2f}s")
        
        return discovery_result
    
    def _detect_transport(self, server_path: str) -> TransportType:
        """
        Auto-detect the transport type based on server characteristics.
        
        Detects transport type based on:
        - HTTP/HTTPS URLs → "sse" (Server-Sent Events over HTTP)
        - Local files → "stdio" (Standard I/O)
        
        Args:
            server_path (str): Path to the server file or HTTP/HTTPS URL
            
        Returns:
            str: Detected transport type ("stdio", "sse", or "http")
            
        Examples:
            _detect_transport("server.py") → "stdio"
            _detect_transport("http://localhost:8000") → "sse"  
            _detect_transport("https://api.example.com/mcp") → "sse"
        """
        # Check if it's an HTTP/HTTPS URL
        if server_path.startswith(("http://", "https://")):
            # Use SSE transport for HTTP URLs (most common for MCP over HTTP)
            return Transport.SSE
        
        # Default to stdio for local files
        return Transport.STDIO
    
    def _build_command(self, server_path: str, transport: TransportType) -> List[str]:
        """
        Build the appropriate command to launch the server or connect to HTTP URL.
        
        For stdio transport:
        - Python files (.py): Uses 'uv run python' if uv project detected, else 'python'
        - JavaScript files (.js, .mjs): Uses 'node'
        - TypeScript files (.ts): Uses 'tsx' (assumes tsx is installed)
        - Other files: Attempts direct execution
        
        For HTTP/SSE transport:
        - Returns URL directly (handled by MCP Inspector's --server-url flag)
        
        Args:
            server_path (str): Path to the server file or HTTP/HTTPS URL
            transport (str): Transport type ("stdio", "sse", "http")
            
        Returns:
            List[str]: Command list suitable for subprocess.run() or URL for HTTP
            
        Examples:
            # Python with uv project
            _build_command('server.py', 'stdio') → ['uv', 'run', 'python', 'server.py']
            
            # HTTP URL
            _build_command('http://localhost:8000', 'sse') → ['http://localhost:8000']
            
            # Node.js
            _build_command('server.js', 'stdio') → ['node', 'server.js']
        """
        # For HTTP/SSE transport, return the URL directly
        if transport in [Transport.SSE, Transport.HTTP] and server_path.startswith(("http://", "https://")):
            return [server_path]
        
        # For stdio transport, handle local files
        server_file = Path(server_path)
        
        # Determine the runtime based on file extension
        if server_file.suffix == ".py":
            # Check if we're in a uv project
            if Path("pyproject.toml").exists() or Path("uv.lock").exists():
                return ["uv", "run", "python", str(server_path)]
            else:
                return ["python", str(server_path)]
        elif server_file.suffix in [".js", ".mjs"]:
            return ["node", str(server_path)]
        elif server_file.suffix == ".ts":
            # Assume tsx is available for TypeScript
            return ["tsx", str(server_path)]
        else:
            # Default to trying to execute directly
            return [str(server_path)]
    
    def _execute_inspector(self, server_cmd: List[str], method: str) -> Dict[str, Any]:
        """
        Execute MCP Inspector CLI and parse the JSON output.
        
        Handles both stdio and HTTP/SSE transports:
        - For stdio: Uses server_cmd as subprocess arguments  
        - For HTTP/SSE: Uses server_cmd[0] as URL with --server-url flag
        
        Args:
            server_cmd: Command to launch server (stdio) or URL list (HTTP/SSE)
            method: Inspector method to call (e.g., "tools/list")
            
        Returns:
            Parsed JSON response from Inspector
            
        Raises:
            DiscoveryError: If Inspector execution fails
        """
        # Check if this is an HTTP URL (server_cmd[0] starts with http)
        if len(server_cmd) == 1 and server_cmd[0].startswith(("http://", "https://")):
            # HTTP/SSE transport - use --server-url
            url = server_cmd[0]
            # Determine transport type based on URL or default to SSE
            transport = Transport.SSE  # Most common for HTTP MCP servers
            
            cmd = [
                "npx",
                "@modelcontextprotocol/inspector",
                "--cli",
                "--transport", transport,
                "--server-url", url,
                "--method", method
            ]
        else:
            # Stdio transport - use server command
            cmd = [
                "npx",
                "@modelcontextprotocol/inspector",
                "--cli"
            ] + server_cmd + [
                "--method",
                method
            ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30  # Increased timeout for HTTP requests
            )
            
            if result.returncode != 0:
                # Check if it's a method not found error (expected for some methods)
                if "Method not found" in result.stderr:
                    return {}
                raise DiscoveryError(
                    f"Inspector failed for method {method}: {result.stderr}"
                )
            
            # Parse JSON output
            try:
                return json.loads(result.stdout)
            except json.JSONDecodeError as e:
                raise DiscoveryError(f"Invalid JSON from Inspector: {e}")
                
        except subprocess.TimeoutExpired:
            raise DiscoveryError(f"Discovery timed out for method {method}")
        except Exception as e:
            raise DiscoveryError(f"Discovery failed: {e}")
    
    def _get_cache_key(self, server_path: str) -> str:
        """
        Generate a cache key for a server path.
        
        Args:
            server_path: Path to the server
            
        Returns:
            Cache key string
        """
        return hashlib.md5(str(server_path).encode()).hexdigest()
    
    def _get_cached_discovery(self, server_path: str) -> Optional[DiscoveryResult]:
        """
        Get cached discovery results if available and not expired.
        
        Args:
            server_path: Path to the server
            
        Returns:
            DiscoveryResult: Cached discovery data or None if not available/expired
        """
        cache_key = self._get_cache_key(server_path)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        if not cache_file.exists():
            return None
        
        try:
            with open(cache_file, "r") as f:
                cached = json.load(f)
            
            # Check if cache is expired
            cached_time = datetime.fromisoformat(cached["metadata"]["discovered_at"])
            age_seconds = (datetime.now() - cached_time).total_seconds()
            
            if age_seconds > self.cache_ttl:
                return None
            
            # Convert to structured model and add cache metadata
            try:
                from .discovery_models import dict_to_discovery_result
            except ImportError:
                from discovery_models import dict_to_discovery_result
            cached_result = dict_to_discovery_result(cached)
            cached_result.metadata.cache_hit = True
            cached_result.metadata.cache_age_seconds = int(age_seconds)
            
            return cached_result
            
        except (json.JSONDecodeError, KeyError):
            # Invalid cache file, ignore it
            return None
    
    def _cache_discovery(self, server_path: str, discovery_data: Dict[str, Any]):
        """
        Cache discovery results.
        
        Args:
            server_path: Path to the server
            discovery_data: Discovery results to cache
        """
        cache_key = self._get_cache_key(server_path)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        try:
            with open(cache_file, "w") as f:
                json.dump(discovery_data, f, indent=2)
        except Exception as e:
            # Caching failure is non-fatal
            print(f"   ⚠️  Failed to cache discovery: {e}")
    
    def clear_cache(self):
        """
        Clear all cached discovery results.
        
        Removes all .json files from the cache directory and reports how many
        files were deleted. This is useful for:
        - Forcing fresh discovery of all servers
        - Cleaning up stale cache data
        - Debugging cache-related issues
        
        Examples:
            engine = DiscoveryEngine()
            engine.clear_cache()  # Prints: "🧹 Cleared 3 cached discovery files"
        """
        count = 0
        for cache_file in self.cache_dir.glob("*.json"):
            cache_file.unlink()
            count += 1
        if count > 0:
            print(f"🧹 Cleared {count} cached discovery files from {self.cache_dir}")
        else:
            print(f"🧹 Cache already empty at {self.cache_dir}")


# Example usage and CLI interface
if __name__ == "__main__":
    """
    Command-line interface for the discovery engine.
    
    Usage:
        python discovery.py <server_path> [--cache] [--transport stdio|http|sse]
    
    Examples:
        python discovery.py mcp_servers/calculator/server.py
        python discovery.py server.py --cache
        python discovery.py server.js --transport http
    """
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python discovery.py <server_path>")
        print("")
        print("Examples:")
        print("  python discovery.py mcp_servers/calculator/server.py")
        print("  python discovery.py server.py  # Fresh discovery, no cache")
        print("")
        print("For more options, use the main CLI:")
        print("  python -m ai_generation.cli --help")
        sys.exit(1)
    
    engine = DiscoveryEngine()
    try:
        result = engine.discover(sys.argv[1])
        # Convert to dict for JSON serialization
        print(json.dumps(result.model_dump(), indent=2, default=str))
        print(f"\n📊 Summary: {result.summary()}")
    except (DependencyError, DiscoveryError) as e:
        print(f"❌ {e}")
        sys.exit(1)