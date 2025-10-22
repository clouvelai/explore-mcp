#!/usr/bin/env python3
"""
Extract non-authenticated MCP servers from remote_mcp_servers.json
"""

import json
from pathlib import Path

def extract_public_servers():
    """Extract servers that don't require authentication"""
    
    # Read the full server list
    with open('remote_mcp_servers.json', 'r') as f:
        all_servers = json.load(f)
    
    # Filter for non-auth servers
    public_servers = []
    for server in all_servers:
        if not server.get('auth_required', True):  # Default to requiring auth if not specified
            # Add tracking fields
            server_with_tracking = server.copy()
            server_with_tracking.update({
                'tested': False,
                'discovery_status': None,  # 'success', 'failed', or None
                'generation_status': None,  # 'success', 'failed', or None
                'discovery_error': None,
                'generation_error': None,
                'test_timestamp': None
            })
            public_servers.append(server_with_tracking)
    
    # Write to public_remote_mcp.json
    with open('public_remote_mcp.json', 'w') as f:
        json.dump(public_servers, f, indent=2)
    
    print(f"Extracted {len(public_servers)} non-authenticated servers to public_remote_mcp.json")
    
    # Print summary
    print("\nPublic servers found:")
    for i, server in enumerate(public_servers, 1):
        print(f"{i:2d}. {server['name']} - {server.get('url', 'Unknown URL')}")

if __name__ == "__main__":
    extract_public_servers()