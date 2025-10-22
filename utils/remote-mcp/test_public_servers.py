#!/usr/bin/env python3
"""
Test public MCP servers by running discovery and generation pipeline
"""

import json
import subprocess
import time
import sys
from datetime import datetime
from pathlib import Path

class PublicServerTester:
    def __init__(self, config_file='public_remote_mcp.json'):
        self.config_file = config_file
        self.servers = []
        self.load_servers()
    
    def load_servers(self):
        """Load server configuration from JSON file"""
        try:
            with open(self.config_file, 'r') as f:
                self.servers = json.load(f)
            print(f"Loaded {len(self.servers)} servers from {self.config_file}")
        except FileNotFoundError:
            print(f"Error: {self.config_file} not found. Run extract_public_servers.py first.")
            sys.exit(1)
    
    def save_servers(self):
        """Save updated server configuration back to JSON file"""
        with open(self.config_file, 'w') as f:
            json.dump(self.servers, f, indent=2)
    
    def get_untested_servers(self):
        """Get list of servers that haven't been tested yet"""
        return [server for server in self.servers if not server.get('tested', False)]
    
    def update_server_status(self, server_index, **updates):
        """Update a server's status fields"""
        self.servers[server_index].update(updates)
        self.servers[server_index]['test_timestamp'] = datetime.now().isoformat()
        self.save_servers()
    
    def run_discovery(self, server_url, server_name):
        """Run discovery on a server"""
        print(f"  Running discovery for {server_name}...")
        
        try:
            # Try discovery first - use discovery.py directly 
            cmd = [
                'uv', 'run', 'python', 'ai_generation/discovery.py',
                server_url
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120  # 2 minute timeout for discovery
            )
            
            if result.returncode == 0:
                print(f"    ✓ Discovery successful")
                return True, None
            else:
                error_msg = result.stderr.strip() or result.stdout.strip()
                print(f"    ✗ Discovery failed: {error_msg}")
                return False, error_msg
                
        except subprocess.TimeoutExpired:
            error_msg = "Discovery timed out after 2 minutes"
            print(f"    ✗ {error_msg}")
            return False, error_msg
        except Exception as e:
            error_msg = f"Discovery error: {str(e)}"
            print(f"    ✗ {error_msg}")
            return False, error_msg
    
    def run_generation(self, server_url, server_name):
        """Run generation on a server"""
        print(f"  Running generation for {server_name}...")
        
        try:
            cmd = [
                'uv', 'run', 'python', '-m', 'ai_generation.cli',
                '--server', server_url,
                '--name', server_name
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout for generation
            )
            
            if result.returncode == 0:
                print(f"    ✓ Generation successful")
                return True, None
            else:
                error_msg = result.stderr.strip() or result.stdout.strip()
                print(f"    ✗ Generation failed: {error_msg}")
                return False, error_msg
                
        except subprocess.TimeoutExpired:
            error_msg = "Generation timed out after 5 minutes"
            print(f"    ✗ {error_msg}")
            return False, error_msg
        except Exception as e:
            error_msg = f"Generation error: {str(e)}"
            print(f"    ✗ {error_msg}")
            return False, error_msg
    
    def get_safe_server_name(self, server):
        """Get a filesystem-safe server name"""
        name = server.get('name', 'unknown').lower()
        # Replace spaces and special chars with hyphens
        safe_name = ''.join(c if c.isalnum() else '-' for c in name)
        # Remove multiple consecutive hyphens
        while '--' in safe_name:
            safe_name = safe_name.replace('--', '-')
        return safe_name.strip('-')
    
    def test_server(self, server_index, server):
        """Test a single server with discovery and generation"""
        name = server.get('name', 'Unknown')
        url = server.get('url', '')
        
        print(f"\n{'='*60}")
        print(f"Testing server {server_index + 1}: {name}")
        print(f"URL: {url}")
        print(f"{'='*60}")
        
        # Skip servers with unknown URLs
        if not url or url == "Unknown - Listed in directories":
            print(f"  ⚠ Skipping {name} - No valid URL")
            self.update_server_status(
                server_index,
                tested=True,
                discovery_status='skipped',
                generation_status='skipped',
                discovery_error='No valid URL provided',
                generation_error='No valid URL provided'
            )
            return
        
        safe_name = self.get_safe_server_name(server)
        
        # Run discovery
        discovery_success, discovery_error = self.run_discovery(url, safe_name)
        
        # Run generation only if discovery succeeded
        generation_success = False
        generation_error = None
        
        if discovery_success:
            generation_success, generation_error = self.run_generation(url, safe_name)
        else:
            generation_error = "Skipped due to discovery failure"
        
        # Update server status
        self.update_server_status(
            server_index,
            tested=True,
            discovery_status='success' if discovery_success else 'failed',
            generation_status='success' if generation_success else 'failed',
            discovery_error=discovery_error,
            generation_error=generation_error
        )
        
        # Print summary for this server
        discovery_status = "✓" if discovery_success else "✗"
        generation_status = "✓" if generation_success else "✗"
        print(f"  Summary: Discovery {discovery_status}, Generation {generation_status}")
    
    def print_progress_summary(self):
        """Print a summary of testing progress"""
        tested_count = sum(1 for s in self.servers if s.get('tested', False))
        total_count = len(self.servers)
        
        discovery_success = sum(1 for s in self.servers if s.get('discovery_status') == 'success')
        generation_success = sum(1 for s in self.servers if s.get('generation_status') == 'success')
        
        print(f"\n{'='*60}")
        print(f"PROGRESS SUMMARY")
        print(f"{'='*60}")
        print(f"Tested: {tested_count}/{total_count} servers")
        print(f"Discovery successes: {discovery_success}")
        print(f"Generation successes: {generation_success}")
        print(f"{'='*60}")
    
    def run_all_tests(self):
        """Run tests on all untested servers"""
        untested = self.get_untested_servers()
        
        if not untested:
            print("All servers have been tested!")
            self.print_progress_summary()
            return
        
        print(f"Starting tests on {len(untested)} untested servers...")
        
        for server in untested:
            # Find the server index in the original list
            server_index = next(i for i, s in enumerate(self.servers) if s == server)
            
            try:
                self.test_server(server_index, server)
                
                # Add a small delay between tests to be respectful
                time.sleep(2)
                
            except KeyboardInterrupt:
                print(f"\n\nInterrupted by user. Progress saved.")
                self.print_progress_summary()
                sys.exit(0)
            except Exception as e:
                print(f"  ✗ Unexpected error testing {server.get('name', 'Unknown')}: {e}")
                self.update_server_status(
                    server_index,
                    tested=True,
                    discovery_status='failed',
                    generation_status='failed',
                    discovery_error=f"Unexpected error: {e}",
                    generation_error="Skipped due to discovery failure"
                )
        
        print(f"\n🎉 All servers tested!")
        self.print_progress_summary()

def main():
    tester = PublicServerTester()
    tester.run_all_tests()

if __name__ == "__main__":
    main()