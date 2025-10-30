"""
MCP Trace Format Specification

This module defines the structured format for capturing MCP client-server
communication in a machine-parsable way for mock server generation.
"""

from dataclasses import dataclass, asdict, field
from typing import Any, Optional, List, Dict
from datetime import datetime
import json


@dataclass
class MCPRequest:
    """Single MCP method invocation"""
    method: str
    args: List[Any] = field(default_factory=list)
    kwargs: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class MCPResponse:
    """Response from MCP server"""
    success: bool
    result: Optional[Any] = None
    error: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class MCPCallPair:
    """Request-response pair for a single MCP call"""
    request: MCPRequest
    response: MCPResponse
    duration_ms: Optional[float] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'request': asdict(self.request),
            'response': asdict(self.response),
            'duration_ms': self.duration_ms
        }


@dataclass
class MCPSession:
    """Complete MCP session with all interactions"""
    session_id: str
    server_info: Dict[str, Any]
    calls: List[MCPCallPair] = field(default_factory=list)
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    ended_at: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'session_id': self.session_id,
            'server_info': self.server_info,
            'calls': [call.to_dict() for call in self.calls],
            'started_at': self.started_at,
            'ended_at': self.ended_at,
            'metadata': self.metadata
        }

    def to_json(self, indent: Optional[int] = 2) -> str:
        """Serialize session to JSON"""
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: dict) -> 'MCPSession':
        """Deserialize session from dictionary"""
        calls = []
        for call_data in data.get('calls', []):
            req = MCPRequest(**call_data['request'])
            resp = MCPResponse(**call_data['response'])
            calls.append(MCPCallPair(
                request=req,
                response=resp,
                duration_ms=call_data.get('duration_ms')
            ))

        return cls(
            session_id=data['session_id'],
            server_info=data['server_info'],
            calls=calls,
            started_at=data['started_at'],
            ended_at=data.get('ended_at'),
            metadata=data.get('metadata', {})
        )

    @classmethod
    def from_json(cls, json_str: str) -> 'MCPSession':
        """Deserialize session from JSON string"""
        return cls.from_dict(json.loads(json_str))


class TraceWriter:
    """Writes MCP sessions to trace files"""

    def __init__(self, output_file: str):
        self.output_file = output_file

    def write_session(self, session: MCPSession, append: bool = True):
        """
        Write a complete session to the trace file

        Format: One JSON object per line (NDJSON) for easy streaming
        """
        mode = 'a' if append else 'w'
        with open(self.output_file, mode) as f:
            f.write(session.to_json(indent=None) + '\n')

    def write_sessions(self, sessions: List[MCPSession]):
        """Write multiple sessions"""
        with open(self.output_file, 'w') as f:
            for session in sessions:
                f.write(session.to_json(indent=None) + '\n')


class TraceReader:
    """Reads MCP sessions from trace files"""

    def __init__(self, trace_file: str):
        self.trace_file = trace_file

    def read_sessions(self) -> List[MCPSession]:
        """Read all sessions from trace file"""
        sessions = []
        with open(self.trace_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    sessions.append(MCPSession.from_json(line))
        return sessions

    def read_latest_session(self) -> Optional[MCPSession]:
        """Read the most recent session from trace file"""
        sessions = self.read_sessions()
        return sessions[-1] if sessions else None
