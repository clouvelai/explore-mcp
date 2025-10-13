"""
DEPRECATED: This module has been moved to mcp_servers/calculator/tools.py

This file is kept for backwards compatibility.
"""

import sys
import os

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the functions from the new location
from mcp_servers.calculator.tools import register_tools, register_prompts

# Make them available for backwards compatibility
__all__ = ['register_tools', 'register_prompts']