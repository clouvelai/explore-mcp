#!/usr/bin/env python3
"""
AI Service - Core AI functionality for generating responses using Claude CLI.

Provides a clean abstraction for interacting with Claude CLI and handling
structured responses.
"""

import json
import re
import subprocess
from typing import Dict, Any, Optional


class ClaudeError(Exception):
    """Base exception for Claude CLI related errors."""
    pass


class ClaudeTimeoutError(ClaudeError):
    """Raised when Claude CLI call times out."""
    pass


class ClaudeNotFoundError(ClaudeError):
    """Raised when Claude CLI is not found in PATH."""
    pass


class ClaudeExecutionError(ClaudeError):
    """Raised when Claude CLI returns non-zero exit code."""
    pass


class AIService:
    """Service for interacting with Claude CLI to generate AI responses."""
    
    def __init__(self, timeout: int = 180):
        """
        Initialize AIService with configurable timeout.
        
        Args:
            timeout: Timeout in seconds for Claude CLI calls (default: 180)
        """
        self.timeout = timeout
    
    def call_claude(self, prompt: str) -> str:
        """
        Call Claude CLI with a prompt and return the raw response.
        
        Args:
            prompt: The prompt to send to Claude
            
        Returns:
            The raw string response from Claude
            
        Raises:
            ValueError: If prompt is empty or None
            ClaudeTimeoutError: If Claude CLI call times out
            ClaudeNotFoundError: If Claude CLI is not found in PATH
            ClaudeExecutionError: If Claude CLI returns non-zero exit code
        """
        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty or None")
        try:
            result = subprocess.run(
                ["claude", prompt],
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            
            if result.returncode != 0:
                raise ClaudeExecutionError(f"Claude CLI failed: {result.stderr}")
            
            return result.stdout.strip()
        
        except subprocess.TimeoutExpired:
            raise ClaudeTimeoutError(f"Claude CLI call timed out after {self.timeout} seconds")
        except FileNotFoundError:
            raise ClaudeNotFoundError("Claude CLI not found. Please ensure 'claude' is installed and in PATH")
    
    def clean_json_response(self, response: str) -> str:
        """
        Clean up JSON response by removing markdown code blocks if present.
        
        Args:
            response: Raw response that may contain markdown formatting
            
        Returns:
            Cleaned JSON string
        """
        # Remove markdown code blocks using regex
        cleaned = re.sub(r'^```(?:json)?\s*', '', response.strip(), flags=re.MULTILINE)
        cleaned = re.sub(r'\s*```$', '', cleaned, flags=re.MULTILINE)
        return cleaned.strip()
    
    def generate_json(self, prompt: str) -> Dict[str, Any]:
        """
        Generate a JSON response from Claude and parse it.
        
        Args:
            prompt: The prompt to send to Claude
            
        Returns:
            Parsed JSON as a dictionary
            
        Raises:
            ValueError: If prompt is empty or None
            json.JSONDecodeError: If response cannot be parsed as JSON
            ClaudeTimeoutError: If Claude CLI call times out
            ClaudeNotFoundError: If Claude CLI is not found in PATH
            ClaudeExecutionError: If Claude CLI returns non-zero exit code
        """
        response = self.call_claude(prompt)
        cleaned_response = self.clean_json_response(response)
        
        try:
            return json.loads(cleaned_response)
        except json.JSONDecodeError as e:
            # Add context to the error
            raise json.JSONDecodeError(
                f"Failed to parse Claude response as JSON: {e.msg}",
                cleaned_response,
                e.pos
            )


def test_claude_cli() -> bool:
    """
    Test if Claude CLI is available and working.
    
    Returns:
        True if Claude CLI is available, False otherwise
    """
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
    # Test the AIService
    import sys
    
    if test_claude_cli():
        print("✅ Claude CLI is available")
        
        # Test basic functionality
        service = AIService()
        try:
            # Simple test prompt
            response = service.call_claude("Say 'Hello, AI Service!' and nothing else.")
            print(f"Test response: {response}")
        except Exception as e:
            print(f"❌ Test failed: {e}")
            sys.exit(1)
    else:
        print("❌ Claude CLI not found or not working")
        sys.exit(1)