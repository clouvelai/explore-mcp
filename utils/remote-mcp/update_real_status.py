#!/usr/bin/env python3
"""
Update public_remote_mcp.json with actual working status based on tools found
"""

import json
import os
import glob

def update_working_status():
    """Update JSON with real working status"""
    
    # Load server status
    with open('public_remote_mcp.json', 'r') as f:
        servers = json.load(f)
    
    working_servers = [
        'Microsoft Learn MCP Server',
        'Semgrep Security Scanner', 
        'GitMCP Dynamic Repository Access',
        'DeepWiki Documentation'
    ]
    
    # Add new fields to track real working status
    for server in servers:
        name = server.get('name', '')
        
        if name in working_servers:
            server['actually_working'] = True
            server['has_tools'] = True
        else:
            server['actually_working'] = False  
            server['has_tools'] = False
            
        # Add note about why non-working servers failed
        if server.get('discovery_status') == 'skipped':
            server['failure_reason'] = 'No valid URL provided'
        elif not server.get('actually_working', False) and server.get('tested', False):
            server['failure_reason'] = 'URL exists but not a proper MCP server (returned 0 tools)'
        else:
            server['failure_reason'] = None
    
    # Save updated JSON
    with open('public_remote_mcp.json', 'w') as f:
        json.dump(servers, f, indent=2)
    
    print("✅ Updated public_remote_mcp.json with actual working status")
    
    # Print summary
    working = sum(1 for s in servers if s.get('actually_working', False))
    tested = sum(1 for s in servers if s.get('tested', False))
    
    print(f"\nSummary:")
    print(f"  Total servers: {len(servers)}")
    print(f"  Tested: {tested}")
    print(f"  Actually working: {working}")
    print(f"  Success rate: {working/tested*100:.1f}%")

if __name__ == "__main__":
    update_working_status()