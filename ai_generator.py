#!/usr/bin/env python3
"""
AI-Powered MCP Evaluation Generator

Uses Claude CLI to intelligently generate mock server responses and evaluation test cases
based on discovered MCP tool schemas.
"""

import json
import subprocess
import sys
from typing import Dict, Any, List


def call_claude_cli(prompt: str) -> str:
    """Call Claude CLI with a prompt and return the response."""
    try:
        # Call claude CLI with the prompt
        result = subprocess.run(
            ["claude", prompt],
            capture_output=True,
            text=True,
            timeout=120  # 2 minute timeout for complex generation
        )
        
        if result.returncode != 0:
            raise Exception(f"Claude CLI failed: {result.stderr}")
        
        return result.stdout.strip()
    
    except subprocess.TimeoutExpired:
        raise Exception("Claude CLI call timed out")
    except FileNotFoundError:
        raise Exception("Claude CLI not found. Please ensure 'claude' is installed and in PATH")
    except Exception as e:
        raise Exception(f"Error calling Claude CLI: {e}")


def generate_ai_mock_responses(tools: List[Dict[str, Any]]) -> Dict[str, str]:
    """Generate mock responses for tools using Claude."""
    print("🤖 Generating AI-powered mock responses...")
    
    # Prepare tool information for Claude
    tools_info = []
    for tool in tools:
        tool_info = {
            "name": tool["name"],
            "description": tool["description"],
            "schema": tool.get("inputSchema", {})
        }
        tools_info.append(tool_info)
    
    prompt = f"""
I need you to generate realistic mock responses for MCP tools. Here are the tools:

{json.dumps(tools_info, indent=2)}

For each tool, generate a realistic mock response string that:
1. Reflects what the tool would actually return
2. Is appropriate for the tool's purpose based on its name and description
3. Includes realistic data (not just "mock_value")
4. Handles mathematical operations with actual calculations when possible

Return ONLY a JSON object mapping tool names to mock response strings. No other text.

Example format:
{{
  "tool_name": "realistic response string",
  "another_tool": "another realistic response"
}}
"""
    
    try:
        response = call_claude_cli(prompt)
        
        # Clean up the response (remove markdown code blocks if present)
        response = response.strip()
        if response.startswith('```json'):
            response = response[7:]  # Remove ```json
        if response.endswith('```'):
            response = response[:-3]  # Remove ```
        response = response.strip()
        
        # Parse the JSON response
        mock_responses = json.loads(response)
        
        print(f"✅ Generated {len(mock_responses)} AI mock responses")
        return mock_responses
    
    except json.JSONDecodeError as e:
        print(f"⚠️  Failed to parse Claude response as JSON: {e}")
        print(f"Raw response: {response}")
        return {}
    except Exception as e:
        print(f"⚠️  Error generating AI mock responses: {e}")
        return {}


def generate_ai_test_cases(tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Generate intelligent test cases using Claude."""
    print("🤖 Generating AI-powered test cases...")
    
    # Prepare tool information for Claude
    tools_info = []
    for tool in tools:
        tool_info = {
            "name": tool["name"],
            "description": tool["description"],
            "schema": tool.get("inputSchema", {})
        }
        tools_info.append(tool_info)
    
    prompt = f"""
I need you to generate comprehensive test cases for MCP tools. Here are the tools:

{json.dumps(tools_info, indent=2)}

For each tool, generate test cases that include:
1. Valid parameter tests with realistic values
2. Missing required parameter tests  
3. Invalid type tests
4. Domain-specific edge cases (e.g., for math tools: division by zero, negative numbers, very large numbers)
5. Boundary condition tests relevant to each tool

Return ONLY a JSON array of test case objects. Each test case should have:
- "tool": tool name
- "test_cases": array of test case objects with:
  - "id": unique test case ID
  - "type": test type (valid_params, missing_required, invalid_type, edge_case)
  - "description": what this test checks
  - "params": parameters to pass to the tool
  - "expected_result": "success", "error", or "any"
  - "expected_contains": array of strings that should appear in the response

Example format:
[
  {{
    "tool": "add",
    "test_cases": [
      {{
        "id": "add_valid_positive",
        "type": "valid_params",
        "description": "Add two positive numbers",
        "params": {{"a": 5.0, "b": 3.0}},
        "expected_result": "success",
        "expected_contains": ["8"]
      }}
    ]
  }}
]
"""
    
    try:
        response = call_claude_cli(prompt)
        
        # Clean up the response (remove markdown code blocks if present)
        response = response.strip()
        if response.startswith('```json'):
            response = response[7:]  # Remove ```json
        if response.endswith('```'):
            response = response[:-3]  # Remove ```
        response = response.strip()
        
        # Parse the JSON response
        test_cases = json.loads(response)
        
        total_cases = sum(len(tool_tests.get("test_cases", [])) for tool_tests in test_cases)
        print(f"✅ Generated {total_cases} AI test cases across {len(test_cases)} tools")
        return test_cases
    
    except json.JSONDecodeError as e:
        print(f"⚠️  Failed to parse Claude response as JSON: {e}")
        print(f"Raw response: {response}")
        return []
    except Exception as e:
        print(f"⚠️  Error generating AI test cases: {e}")
        return []


def test_claude_cli() -> bool:
    """Test if Claude CLI is available and working."""
    try:
        result = subprocess.run(
            ["claude", "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode == 0
    except:
        return False


if __name__ == "__main__":
    # Test Claude CLI availability
    if test_claude_cli():
        print("✅ Claude CLI is available")
    else:
        print("❌ Claude CLI not found or not working")
        sys.exit(1)