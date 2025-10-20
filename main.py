"""
Main entry point for the MCP chat backend.
This provides backward compatibility with the original chat_backend.py.
"""

from backend.app import run_app

if __name__ == '__main__':
    run_app()