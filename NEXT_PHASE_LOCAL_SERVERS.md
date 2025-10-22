# Next Phase: Local Server Auto-Discovery

## Current State
- ✅ Unified MCP server registry implemented
- ✅ Calculator server migrated as example
- ✅ Remote servers (Microsoft Learn) working in unified system

## Next Phase Improvements

### 1. Auto-Discovery of Local Servers
**Goal**: Automatically discover and add all local servers from `mcp_servers/` directory

**Implementation**:
```bash
# Future command
python -m ai_generation.cli server auto-discover-local
```

**Features**:
- Scan `mcp_servers/` for `server.py` files
- Auto-generate server IDs from directory names
- Extract server metadata (name, description) from server files
- Add all discovered servers to unified registry

### 2. Migrate Remaining Local Servers
**Current local servers to migrate**:
- `mcp_servers/air_fryer/server.py`
- `mcp_servers/gmail/server.py` 
- `mcp_servers/google_drive/server.py`

**Process**:
1. Auto-discover all local servers
2. Run discovery on each server
3. Generate mock servers for all
4. Verify all servers work in unified system

### 3. Enhanced Server Management
**Future CLI commands**:
```bash
# Auto-discover and add all local servers
python -m ai_generation.cli server auto-discover-local

# Migrate all local servers to unified system
python -m ai_generation.cli server migrate-local

# Bulk operations
python -m ai_generation.cli server discover-all --type local
python -m ai_generation.cli server generate-all --type local
```

## Benefits
- **Zero manual configuration** for local servers
- **Consistent management** of all server types
- **Easy onboarding** of new local servers
- **Bulk operations** for maintenance

## Current Working Example
The calculator server demonstrates the unified system:
- ✅ Added via CLI: `server add calculator --type local --path "mcp_servers/calculator/server.py"`
- ✅ Discovered: `server discover calculator`
- ✅ Generated: `server generate calculator`
- ✅ Status: `server status calculator`

This proves the unified system works perfectly for local servers!
