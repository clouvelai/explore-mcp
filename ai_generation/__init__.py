"""
AI Generation Module

This module provides AI-powered generation of mock MCP servers and evaluation test cases.

Main components:
- ai_service: Core Claude CLI interface
- cli: Main command-line interface
- server_generator: Generates mock MCP servers
- evals_generator: Generates evaluation test cases
- evaluation_runner: Runs evaluations against servers
"""

from .ai_service import AIService, test_claude_cli
from .evals_generator import generate_ai_test_cases
from .server_generator import generate_ai_mock_responses, generate_ai_mock_server

__all__ = [
    "AIService",
    "test_claude_cli", 
    "generate_ai_mock_server",
    "generate_ai_mock_responses",
    "generate_ai_test_cases",
]