"""
OpenAI service for handling chat completions.
"""

import json

from openai import OpenAI


class OpenAIService:
    """Service for OpenAI chat completions."""
    
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
    
    def chat_completion(self, messages: list, tools: list = None, model: str = "gpt-4o-mini"):
        """Create a chat completion with optional tools."""
        return self.client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools if tools else None,
            tool_choice="auto" if tools else None,
        )
    
    def chat_completion_with_tools(self, messages: list, model: str = "gpt-4o-mini"):
        """Create a chat completion for final response after tool calls."""
        return self.client.chat.completions.create(
            model=model,
            messages=messages,
        )