#!/usr/bin/env python3
"""
AI-Powered MCP Evaluation Generator

Compatibility shim for backward compatibility.
Delegates to the new modular architecture while maintaining the same interface.
"""

import sys

# Re-export functions from new modules to maintain backward compatibility
from mcp_server_generator import generate_ai_mock_responses
from mcp_evals_generator import generate_ai_test_cases
from ai_service import test_claude_cli

# Note: This module is maintained for backward compatibility.
# New code should import directly from the specific modules:
#   - mcp_server_generator for mock server generation
#   - mcp_evals_generator for evaluation test case generation
#   - ai_service for Claude CLI utilities


if __name__ == "__main__":
    # Test Claude CLI availability
    if test_claude_cli():
        print("✅ Claude CLI is available")
    else:
        print("❌ Claude CLI not found or not working")
        sys.exit(1)