#!/usr/bin/env python3
"""
Verify the actual results from discovery vs JSON status
"""

import json
import os
import glob

def verify_discovery_results():
    """Check actual tool discovery results"""
    
    # Load server status
    with open('public_remote_mcp.json', 'r') as f:
        servers = json.load(f)
    
    print("="*80)
    print("DISCOVERY VERIFICATION RESULTS")
    print("="*80)
    
    actual_working_servers = []
    
    for server in servers:
        name = server.get('name', 'Unknown')
        url = server.get('url', 'Unknown')
        tested = server.get('tested', False)
        discovery_status = server.get('discovery_status', 'Unknown')
        
        if not tested:
            print(f"❌ NOT TESTED: {name}")
            continue
            
        if discovery_status == 'skipped':
            print(f"⏭️  SKIPPED: {name} (No valid URL)")
            continue
        
        # Find corresponding generated directory
        safe_name = ''.join(c if c.isalnum() else '-' for c in name.lower())
        while '--' in safe_name:
            safe_name = safe_name.replace('--', '-')
        safe_name = safe_name.strip('-')
        
        # Look for discovery.json files
        discovery_files = glob.glob(f"generated/*{safe_name}*/discovery.json") + \
                         glob.glob(f"generated/**/discovery.json")
        
        tools_found = 0
        discovery_file_found = False
        
        for disc_file in discovery_files:
            try:
                with open(disc_file, 'r') as f:
                    discovery_data = json.load(f)
                    if discovery_data.get('server_path') == url or \
                       url in discovery_data.get('server_path', ''):
                        tools_found = len(discovery_data.get('tools', []))
                        discovery_file_found = True
                        break
            except:
                continue
        
        if not discovery_file_found:
            # Try manual pattern matching
            for disc_file in glob.glob("generated/*/discovery.json"):
                try:
                    with open(disc_file, 'r') as f:
                        discovery_data = json.load(f)
                        dir_name = os.path.basename(os.path.dirname(disc_file))
                        if safe_name in dir_name.lower():
                            tools_found = len(discovery_data.get('tools', []))
                            discovery_file_found = True
                            break
                except:
                    continue
        
        status_icon = "✅" if tools_found > 0 else "⚠️ "
        
        if tools_found > 0:
            actual_working_servers.append({
                'name': name,
                'url': url,
                'tools_count': tools_found
            })
        
        print(f"{status_icon} {name}")
        print(f"    URL: {url}")
        print(f"    Status: {discovery_status}")
        print(f"    Tools found: {tools_found}")
        print()
    
    print("="*80)
    print("SUMMARY")
    print("="*80)
    
    total_tested = sum(1 for s in servers if s.get('tested', False))
    skipped_count = sum(1 for s in servers if s.get('discovery_status') == 'skipped')
    working_count = len(actual_working_servers)
    
    print(f"Total servers: {len(servers)}")
    print(f"Tested: {total_tested}")
    print(f"Skipped (no URL): {skipped_count}")
    print(f"Actually working with tools: {working_count}")
    print()
    
    print("WORKING MCP SERVERS:")
    for server in actual_working_servers:
        print(f"  ✅ {server['name']} ({server['tools_count']} tools)")
        print(f"     {server['url']}")
    
    print("="*80)

if __name__ == "__main__":
    verify_discovery_results()