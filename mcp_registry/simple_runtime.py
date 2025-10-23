"""
Simple Runtime - Elegant file extension based execution.

The entire "runtime system" in 20 lines instead of 400+.
Uses MCP Inspector for all supported runtimes when available.
"""

import shutil
from pathlib import Path
from typing import List, Optional


def get_execution_command(file_path: Path) -> Optional[List[str]]:
    """Get execution command based on file extension. That's it."""
    
    if not file_path.exists():
        return None
    
    suffix = file_path.suffix.lower()
    has_npx = shutil.which("npx") is not None
    
    if suffix == '.py':
        return ["python", str(file_path)]
    elif suffix == '.ts':
        # TypeScript: MCP Inspector required
        if has_npx:
            return ["npx", "@modelcontextprotocol/inspector", str(file_path)]
        return None
    elif suffix == '.js':
        # Node.js: Prefer MCP Inspector, fallback to node
        if has_npx:
            return ["npx", "@modelcontextprotocol/inspector", str(file_path)]
        return ["node", str(file_path)]
    
    return None


def can_execute(file_path: Path) -> bool:
    """Check if we can execute this file."""
    return get_execution_command(file_path) is not None


def get_runtime_type(file_path: Path) -> Optional[str]:
    """Get runtime type from file extension."""
    suffix = file_path.suffix.lower()
    if suffix == '.py':
        return 'python'
    elif suffix == '.ts':
        return 'typescript'
    elif suffix == '.js':
        return 'nodejs'
    return None


# That's literally the entire runtime system we need.