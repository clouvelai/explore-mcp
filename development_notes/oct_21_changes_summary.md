# October 21, 2025 - Changes Summary

## Major Features Added

### 🔍 HTTP Transport Support (#12)
- **HTTP MCP Server Discovery**: Added full support for discovering and connecting to HTTP-based MCP servers
- **Automatic Transport Detection**: Platform now auto-detects optimal transport (HTTP/SSE/stdio) with intelligent fallback
- **Microsoft Learn Integration**: Added support for Microsoft's public MCP documentation server
- **Air Fryer Example**: New HTTP MCP server example demonstrating HTTP transport capabilities

### 📊 Dual Hash Change Detection (#13)
- **Enhanced Discovery Intelligence**: Implemented dual hash system for precise change detection
  - `server_file_hash`: MD5 of local server files
  - `discovery_content_hash`: MD5 of API schema (primary for all server types)
- **Smarter Regeneration**: Only regenerates mocks when actual server capabilities change

### 📁 MCP Resources Support (#11)
- **Resource Generation**: Full support for MCP resource discovery and mock generation
- **Static Content**: Added realistic mock resource content generation with new prompt system
- **Calculator Resources**: Implemented comprehensive resource examples with documentation

### 🏗️ MCP Inspector Integration (#10)
- **Pydantic Models**: Migrated to structured discovery using Pydantic for better type safety
- **Discovery JSON**: Auto-saves complete discovery metadata during generation process
- **Enhanced Metadata**: Richer server capability detection and documentation

## Infrastructure Improvements

### 🧹 Code Quality
- Fixed multiline string escaping in generated mock tools
- Removed calculator-specific bias from mock response prompts (v1.0.1)
- Updated `.gitignore` for test directories and cleaned up test artifacts

### 📚 Documentation
- Updated `CLAUDE.md` with Microsoft Learn server examples
- Added comprehensive HTTP transport usage patterns
- Enhanced CLI documentation with public server examples

## Pull Requests Merged
- #8: Mock response prompt improvements
- #9: Discovery data persistence 
- #10: MCP Inspector-based discovery
- #11: Resource support implementation
- #12: HTTP transport and public server support
- #13: Dual hash change detection system

## Impact
These changes significantly expand the platform's capability to work with **any MCP server** (local, HTTP, or public) while providing intelligent change detection and comprehensive resource support. The platform now supports the full MCP specification with production-ready discovery and generation capabilities.