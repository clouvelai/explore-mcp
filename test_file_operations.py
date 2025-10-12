#!/usr/bin/env python3
"""
Test script for Google Drive file operations
This script tests the new read_file, edit_file, and create_text_file tools
"""

import asyncio
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def test_google_drive_file_operations():
    """Test the Google Drive file operation tools"""
    
    # Start the Google Drive MCP server
    server_params = StdioServerParameters(
        command="uv", 
        args=["run", "python", "google_drive_mcp_server.py"]
    )
    
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                
                # Initialize the connection
                await session.initialize()
                
                # List available tools
                tools = await session.list_tools()
                print("Available tools:")
                for tool in tools.tools:
                    print(f"  - {tool.name}: {tool.description}")
                
                print("\n" + "="*50)
                print("Testing file operations...")
                print("="*50)
                
                # Test 1: List some files first to get a file ID for testing
                print("\n1. Testing list_files to get file IDs...")
                result = await session.call_tool("list_files", {"max_results": 5})
                if result.content:
                    for content in result.content:
                        if hasattr(content, 'text'):
                            print(content.text)
                
                # Test 2: Create a new test file
                print("\n2. Testing create_text_file...")
                test_content = "Hello from MCP!\nThis is a test file created by the Google Drive MCP server.\nTimestamp: " + str(asyncio.get_event_loop().time())
                
                result = await session.call_tool("create_text_file", {
                    "name": "mcp_test_file.txt",
                    "content": test_content
                })
                
                if result.content:
                    for content in result.content:
                        if hasattr(content, 'text'):
                            print(content.text)
                            # Extract file ID from the response
                            if "File ID:" in content.text:
                                file_id = content.text.split("File ID: ")[1].split("\n")[0]
                                print(f"\nCreated file with ID: {file_id}")
                                
                                # Test 3: Read the file we just created
                                print("\n3. Testing read_file...")
                                read_result = await session.call_tool("read_file", {"file_id": file_id})
                                if read_result.content:
                                    for read_content in read_result.content:
                                        if hasattr(read_content, 'text'):
                                            print(read_content.text)
                                
                                # Test 4: Edit the file
                                print("\n4. Testing edit_file...")
                                new_content = test_content + "\n\nThis line was added by edit_file!"
                                edit_result = await session.call_tool("edit_file", {
                                    "file_id": file_id,
                                    "content": new_content
                                })
                                
                                if edit_result.content:
                                    for edit_content in edit_result.content:
                                        if hasattr(edit_content, 'text'):
                                            print(edit_content.text)
                                
                                # Test 5: Read the file again to verify the edit
                                print("\n5. Re-reading file to verify edit...")
                                read_result2 = await session.call_tool("read_file", {"file_id": file_id})
                                if read_result2.content:
                                    for read_content2 in read_result2.content:
                                        if hasattr(read_content2, 'text'):
                                            print(read_content2.text)
                
                print("\n" + "="*50)
                print("File operations test completed!")
                print("="*50)
                
    except Exception as e:
        print(f"Error during testing: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("Google Drive File Operations Test")
    print("=" * 50)
    print("This script tests the new read_file, edit_file, and create_text_file tools")
    print("Make sure you have:")
    print("1. Set up Google OAuth credentials in .env file")
    print("2. Have valid Google Drive access tokens")
    print("=" * 50)
    
    try:
        result = asyncio.run(test_google_drive_file_operations())
        if result:
            print("\n✅ All tests completed successfully!")
            sys.exit(0)
        else:
            print("\n❌ Tests failed!")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        sys.exit(1)