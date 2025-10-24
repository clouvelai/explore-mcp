#!/usr/bin/env python3
"""
Filesystem MCP Server Interceptor

Connects to the local filesystem MCP server using MITM interception
and saves logs to the mcp-registry directory alongside config.json and discovery.json
"""

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path

# IMPORTANT: Install interceptor BEFORE importing ClientSession
from mcp_interceptor.mcp_interceptor import install_interceptor

# Set up logging to filesystem server registry directory
registry_dir = Path("mcp_registry/servers/filesystem")
log_file = registry_dir / "intercepted_logs.jsonl"
install_interceptor(
    log_file=str(log_file),
    verbose=True
)

# Now import MCP components (ClientSession is now intercepted)
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def test_filesystem_server():
    """Test the filesystem server with various operations and log everything"""
    
    # Get binary path from config
    config_path = registry_dir / "config.json"
    with open(config_path) as f:
        config = json.load(f)
    
    binary_path = config["source"]["binary_path"]
    
    print(f"🔌 Connecting to filesystem server at: {binary_path}")
    print(f"📝 Logging all communications to: {log_file}")
    
    # Connect using stdio transport with proper parameters and allowed directories
    current_dir = os.getcwd()
    server_params = StdioServerParameters(
        command=binary_path,
        args=[current_dir, "/private/tmp"]  # Allow current directory and /private/tmp for testing
    )
    async with stdio_client(server_params) as (reader, writer):
        async with ClientSession(reader, writer) as session:
            print("\n🚀 Starting intercepted filesystem server testing...")
            
            # Initialize session
            await session.initialize()
            
            # List available tools
            print("\n📋 Discovering tools...")
            tools = await session.list_tools()
            print(f"Found {len(tools.tools)} tools:")
            for tool in tools.tools:
                print(f"  - {tool.name}: {tool.description}")
            
            # List available resources
            print("\n📁 Discovering resources...")
            try:
                resources = await session.list_resources()
                print(f"Found {len(resources.resources)} resources:")
                for resource in resources.resources:
                    print(f"  - {resource.uri}: {resource.name}")
            except Exception as e:
                print(f"No resources available: {e}")
            
            # Test file operations
            print("\n🔍 Testing file operations...")
            
            # Test read_file with current directory
            try:
                result = await session.call_tool("read_file", {
                    "path": "README.md"
                })
                print(f"✅ read_file: Success (read {len(str(result))} chars)")
            except Exception as e:
                print(f"❌ read_file: {e}")
            
            # Test list_directory
            try:
                result = await session.call_tool("list_directory", {
                    "path": "."
                })
                print(f"✅ list_directory: Success (found {len(result.content)} items)")
            except Exception as e:
                print(f"❌ list_directory: {e}")
            
            # Test search_files
            try:
                result = await session.call_tool("search_files", {
                    "path": ".",
                    "pattern": "*.py"
                })
                print(f"✅ search_files: Success")
            except Exception as e:
                print(f"❌ search_files: {e}")
            
            # Test write_file (in temp location)
            try:
                temp_file = "/private/tmp/mcp_test_file.txt"
                result = await session.call_tool("write_file", {
                    "path": temp_file,
                    "content": f"Test file created by MCP interceptor at {datetime.now()}"
                })
                print(f"✅ write_file: Success (wrote to {temp_file})")
                
                # Clean up
                os.unlink(temp_file)
            except Exception as e:
                print(f"❌ write_file: {e}")
    
    # Create summary metadata file
    summary_file = registry_dir / "interception_summary.json"
    summary = {
        "timestamp": datetime.now().isoformat(),
        "log_file": str(log_file.name),
        "server_binary": binary_path,
        "operations_tested": [
            "initialize",
            "list_tools", 
            "list_resources",
            "read_file",
            "list_directory", 
            "search_files",
            "write_file"
        ],
        "log_entries_count": count_log_entries(log_file)
    }
    
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n✅ Interception complete!")
    print(f"📊 Summary saved to: {summary_file}")
    print(f"📝 Detailed logs saved to: {log_file}")
    print(f"🗂️  Registry directory contents:")
    for item in registry_dir.iterdir():
        if item.is_file():
            print(f"   - {item.name}")

def count_log_entries(log_file: Path) -> int:
    """Count number of log entries in the JSONL file"""
    try:
        with open(log_file) as f:
            return sum(1 for line in f if line.strip())
    except FileNotFoundError:
        return 0

if __name__ == "__main__":
    # Ensure registry directory exists
    registry_dir.mkdir(parents=True, exist_ok=True)
    
    asyncio.run(test_filesystem_server())