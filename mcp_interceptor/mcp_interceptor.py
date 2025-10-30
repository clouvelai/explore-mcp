"""
MCP Client Communication Interceptor

This module provides transparent interception of all MCP client-server communication
by monkeypatching the ClientSession class from the MCP SDK.
"""

import asyncio
import json
import uuid
import time
from typing import Any, Callable, Optional
from datetime import datetime
from mcp import ClientSession
from mcp_interceptor.trace_format import (
    MCPSession, MCPRequest, MCPResponse, MCPCallPair, TraceWriter
)


class InterceptionLogger:
    """Handles logging of intercepted MCP communications"""

    def __init__(self, log_file: Optional[str] = None, verbose: bool = True,
                 trace_file: Optional[str] = None):
        self.log_file = log_file
        self.trace_file = trace_file
        self.verbose = verbose
        self.request_count = 0
        self.response_count = 0

        # Session tracking for structured trace
        self.current_session: Optional[MCPSession] = None
        self.trace_writer = TraceWriter(trace_file) if trace_file else None
        self._pending_requests: dict = {}  # method -> (request, start_time)

    def start_session(self, server_info: dict = None):
        """Start a new MCP session"""
        self.current_session = MCPSession(
            session_id=str(uuid.uuid4()),
            server_info=server_info or {},
            metadata={}
        )

    def end_session(self):
        """End current session and write to trace file"""
        if self.current_session and self.trace_writer:
            self.current_session.ended_at = datetime.now().isoformat()
            self.trace_writer.write_session(self.current_session)
        self.current_session = None

    def log_request(self, method: str, *args, **kwargs):
        """Log outgoing requests to MCP server"""
        self.request_count += 1
        timestamp = datetime.now().isoformat()

        # Legacy NDJSON format
        log_entry = {
            "type": "request",
            "timestamp": timestamp,
            "count": self.request_count,
            "method": method,
            "args": self._serialize(args),
            "kwargs": self._serialize(kwargs)
        }
        self._write_log(log_entry)

        # Structured session format
        if self.current_session is not None:
            request = MCPRequest(
                method=method,
                args=list(args),
                kwargs=dict(kwargs),
                timestamp=timestamp
            )
            self._pending_requests[method] = (request, time.time())

    def log_response(self, method: str, result: Any, error: Optional[Exception] = None):
        """Log responses from MCP server"""
        self.response_count += 1
        timestamp = datetime.now().isoformat()

        # Legacy NDJSON format
        log_entry = {
            "type": "response",
            "timestamp": timestamp,
            "count": self.response_count,
            "method": method,
            "result": self._serialize(result) if not error else None,
            "error": str(error) if error else None
        }
        self._write_log(log_entry)

        # Structured session format
        if self.current_session is not None and method in self._pending_requests:
            request, start_time = self._pending_requests.pop(method)
            duration_ms = (time.time() - start_time) * 1000

            response = MCPResponse(
                success=error is None,
                result=self._serialize(result) if not error else None,
                error=str(error) if error else None,
                timestamp=timestamp
            )

            call_pair = MCPCallPair(
                request=request,
                response=response,
                duration_ms=duration_ms
            )
            self.current_session.calls.append(call_pair)

    def _serialize(self, obj: Any) -> Any:
        """Convert objects to JSON-serializable format"""
        if hasattr(obj, '__dict__'):
            return {
                "_type": obj.__class__.__name__,
                **{k: self._serialize(v) for k, v in obj.__dict__.items() if not k.startswith('_')}
            }
        elif isinstance(obj, (list, tuple)):
            return [self._serialize(item) for item in obj]
        elif isinstance(obj, dict):
            return {k: self._serialize(v) for k, v in obj.items()}
        elif isinstance(obj, (str, int, float, bool, type(None))):
            return obj
        else:
            return str(obj)

    def _write_log(self, entry: dict):
        """Write log entry to file and/or console"""
        if self.verbose:
            print(f"\n{'='*80}")
            print(f"[MCP {entry['type'].upper()}] {entry['method']}")
            print(f"Timestamp: {entry['timestamp']}")
            if entry['type'] == 'request':
                if entry['args']:
                    print(f"Args: {json.dumps(entry['args'], indent=2)}")
                if entry['kwargs']:
                    print(f"Kwargs: {json.dumps(entry['kwargs'], indent=2)}")
            else:
                if entry['error']:
                    print(f"Error: {entry['error']}")
                elif entry['result']:
                    print(f"Result: {json.dumps(entry['result'], indent=2)}")
            print(f"{'='*80}\n")

        if self.log_file:
            with open(self.log_file, 'a') as f:
                f.write(json.dumps(entry) + '\n')


class InterceptedClientSession(ClientSession):
    """
    Monkeypatched version of ClientSession that intercepts all communication
    """

    _logger: Optional[InterceptionLogger] = None
    _request_hooks: list[Callable] = []
    _response_hooks: list[Callable] = []

    @classmethod
    def set_logger(cls, logger: InterceptionLogger):
        """Set the global logger for all intercepted sessions"""
        cls._logger = logger

    @classmethod
    def add_request_hook(cls, hook: Callable):
        """Add a custom hook that runs before each request"""
        cls._request_hooks.append(hook)

    @classmethod
    def add_response_hook(cls, hook: Callable):
        """Add a custom hook that runs after each response"""
        cls._response_hooks.append(hook)

    async def _intercept_call(self, method_name: str, original_method, *args, **kwargs):
        """Wrap any method call with interception logic"""
        # Log request
        if self._logger:
            self._logger.log_request(method_name, *args, **kwargs)

        # Run request hooks
        for hook in self._request_hooks:
            await hook(method_name, args, kwargs) if asyncio.iscoroutinefunction(hook) else hook(method_name, args, kwargs)

        # Execute original method
        error = None
        result = None
        try:
            result = await original_method(*args, **kwargs)
        except Exception as e:
            error = e
            if self._logger:
                self._logger.log_response(method_name, None, error)
            raise

        # Log response
        if self._logger:
            self._logger.log_response(method_name, result)

        # Run response hooks
        for hook in self._response_hooks:
            await hook(method_name, result) if asyncio.iscoroutinefunction(hook) else hook(method_name, result)

        return result

    # Intercept all key MCP client methods
    async def initialize(self):
        """Intercept initialize"""
        return await self._intercept_call('initialize', super().initialize)

    async def list_tools(self):
        """Intercept list_tools"""
        return await self._intercept_call('list_tools', super().list_tools)

    async def call_tool(self, *args, **kwargs):
        """Intercept call_tool"""
        return await self._intercept_call('call_tool', super().call_tool, *args, **kwargs)

    async def list_resources(self):
        """Intercept list_resources"""
        return await self._intercept_call('list_resources', super().list_resources)

    async def read_resource(self, *args, **kwargs):
        """Intercept read_resource"""
        return await self._intercept_call('read_resource', super().read_resource, *args, **kwargs)

    async def list_prompts(self):
        """Intercept list_prompts"""
        return await self._intercept_call('list_prompts', super().list_prompts)

    async def get_prompt(self, *args, **kwargs):
        """Intercept get_prompt"""
        return await self._intercept_call('get_prompt', super().get_prompt, *args, **kwargs)

    async def send_roots_list_changed(self):
        """Intercept send_roots_list_changed"""
        return await self._intercept_call('send_roots_list_changed', super().send_roots_list_changed)


def install_interceptor(log_file: Optional[str] = None, verbose: bool = True,
                       trace_file: Optional[str] = None):
    """
    Install the MCP client interceptor globally

    Args:
        log_file: Optional file path to write legacy NDJSON logs
        verbose: Whether to print intercepted communications to console
        trace_file: Optional file path to write structured session traces

    Returns:
        InterceptionLogger instance for further configuration
    """
    import mcp
    import mcp.client.session

    # Create logger
    logger = InterceptionLogger(log_file=log_file, verbose=verbose, trace_file=trace_file)

    # Set logger on intercepted class
    InterceptedClientSession.set_logger(logger)

    # Replace ClientSession in both the mcp module and mcp.client.session module
    mcp.ClientSession = InterceptedClientSession
    mcp.client.session.ClientSession = InterceptedClientSession

    return logger


def uninstall_interceptor():
    """
    Restore original ClientSession (removes interception)
    """
    import mcp
    from mcp.client.session import ClientSession as OriginalClientSession

    mcp.ClientSession = OriginalClientSession
