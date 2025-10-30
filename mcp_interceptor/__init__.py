"""
MCP Interceptor & Mock Generator Package

Provides tools for capturing MCP client-server communication and generating
mock servers from recorded traces.
"""

from .mcp_interceptor import (
    InterceptionLogger,
    InterceptedClientSession,
    install_interceptor,
    uninstall_interceptor
)

from .trace_format import (
    MCPSession,
    MCPRequest,
    MCPResponse,
    MCPCallPair,
    TraceWriter,
    TraceReader
)

from .mock_generator import MockServerGenerator

__all__ = [
    # Interceptor
    'InterceptionLogger',
    'InterceptedClientSession',
    'install_interceptor',
    'uninstall_interceptor',
    # Trace format
    'MCPSession',
    'MCPRequest',
    'MCPResponse',
    'MCPCallPair',
    'TraceWriter',
    'TraceReader',
    # Generator
    'MockServerGenerator',
]

__version__ = '1.0.0'
