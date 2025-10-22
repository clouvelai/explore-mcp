#!/usr/bin/env python3
"""
Monitor the progress of public server testing
"""

import json
import time

def monitor_progress():
    """Monitor testing progress"""
    
    try:
        with open('public_remote_mcp.json', 'r') as f:
            servers = json.load(f)
    except FileNotFoundError:
        print("public_remote_mcp.json not found")
        return
    
    total = len(servers)
    tested = sum(1 for s in servers if s.get('tested', False))
    discovery_success = sum(1 for s in servers if s.get('discovery_status') == 'success')
    generation_success = sum(1 for s in servers if s.get('generation_status') == 'success')
    
    print(f"{'='*60}")
    print(f"TESTING PROGRESS SUMMARY")
    print(f"{'='*60}")
    print(f"Total servers: {total}")
    print(f"Tested: {tested} ({tested/total*100:.1f}%)")
    print(f"Discovery successes: {discovery_success}")
    print(f"Generation successes: {generation_success}")
    print(f"Remaining: {total - tested}")
    print(f"{'='*60}")
    
    print("\nTested servers:")
    for server in servers:
        if server.get('tested', False):
            name = server.get('name', 'Unknown')
            discovery = server.get('discovery_status', 'Unknown')
            generation = server.get('generation_status', 'Unknown')
            timestamp = server.get('test_timestamp', 'Unknown')
            print(f"  ✓ {name}")
            print(f"    Discovery: {discovery}, Generation: {generation}")
            print(f"    Tested at: {timestamp}")
    
    print(f"\nNext servers to test:")
    count = 0
    for server in servers:
        if not server.get('tested', False):
            name = server.get('name', 'Unknown')
            url = server.get('url', 'Unknown')
            print(f"  - {name} ({url})")
            count += 1
            if count >= 3:  # Show next 3
                break

if __name__ == "__main__":
    monitor_progress()