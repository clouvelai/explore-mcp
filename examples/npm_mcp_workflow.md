# NPM MCP Server Workflow

This guide shows how to add, discover, and test npm-published MCP servers using the unified MCP CLI.

## 📦 Complete NPM MCP Server Workflow

### **🚀 Quick Start (Recommended)**
```bash
# One command to add + discover + generate
./mcp add memory @modelcontextprotocol/server-memory --source npm --category "Memory"
./mcp sync  # Discovers all new servers and generates mocks
./mcp test memory
```

### **📋 Step-by-Step Workflow**

**1. Add NPM Server**
```bash
./mcp add filesystem @modelcontextprotocol/server-filesystem \
  --source npm \
  --category "Storage" \
  --description "File system operations MCP server"
```
- ✅ **Auto-installs npm package** globally (`npm install -g`)
- ✅ **Detects binary location** in PATH
- ✅ **Captures package version** from npm registry
- ✅ **Creates directory structure** in `mcp_registry/servers/filesystem/`

**2. Inspect Configuration**
```bash
./mcp inspect filesystem
```
Shows:
- Package name and version from npm
- Binary name and installation path
- Server metadata and provider info

**3. Discover Package Capabilities**
```bash
./mcp discover filesystem
```
- 🔌 **Connects to installed binary** via stdio
- 📡 **Discovers tools, resources, prompts** 
- 💾 **Saves discovery.json** with full API schema
- 🔐 **Tracks content hash** for change detection

**4. Generate Mock Server**
```bash
./mcp generate filesystem
```
- 🤖 **AI generates realistic mock responses** using Claude
- 📝 **Creates mock server** (`generated/server.py`)
- 🧪 **Creates test suite** (`generated/evaluations.json`)

**5. Test Mock Server**
```bash
./mcp test filesystem
```
- 🔬 **Runs evaluation suite** against generated mock
- ✅ **Validates tool calls** and response formats
- 📊 **Reports pass/fail results**

## 🎯 Real Example: Filesystem Server

Here's a complete example using the official ModelContextProtocol filesystem server:

```bash
# Add filesystem operations server from npm
./mcp add fs @modelcontextprotocol/server-filesystem \
  --source npm \
  --category "Storage" \
  --description "File system operations server"

# Expected output:
# 📦 Installing npm package: @modelcontextprotocol/server-filesystem
# ✅ Package installed successfully
# 🔍 Found binary: mcp-server-filesystem at /usr/local/bin/mcp-server-filesystem
# 📋 Package version: 2025.8.21
# ✅ Added server: fs (fs)
#    Type: npm
#    Package: @modelcontextprotocol/server-filesystem
#    Binary: /usr/local/bin/mcp-server-filesystem

# Inspect the configuration
./mcp inspect fs

# Expected output:
# 📋 Server: fs
# ==================================================
# Name: fs
# Description: File system operations server
# Category: Storage
# Provider: npm
# Version: 1.0.0
# 
# 📍 Source:
# Type: npm
# Package: @modelcontextprotocol/server-filesystem
# Version: 2025.8.21
# Binary: mcp-server-filesystem
# Binary Path: /usr/local/bin/mcp-server-filesystem
# Transport: stdio

# Discover capabilities
./mcp discover fs

# Expected output:
# 📡 Discovering server 'fs'...
# 🔍 Discovering MCP server: /usr/local/bin/mcp-server-filesystem
#    Transport: stdio
#    ✓ Found 14 tools
#    ✓ Found 0 resources
#    ✓ Found 0 prompts
# ✅ Discovery completed for 'fs'

# Generate mock server
./mcp generate fs

# Expected output:
# 🔨 Generating mocks for server 'fs'...
# 🤖 Generating AI-powered mock responses...
# ✅ Generated tools.py with 14 tools
# ✅ Generated server.py
# ✅ Generation completed for 'fs'

# Test the mock
./mcp test fs

# Check status
./mcp status

# Expected output:
# 📊 MCP Registry Status
# ==================================================
# Total servers: 7
# Discovered: 5/7
# Generated: 5/7
# 
# 📂 By Category:
#   Storage: 2
#   Memory: 1
#   ...

# Clean up (optional)
./mcp remove fs
```

## 🎯 Popular NPM MCP Servers

### **Memory Operations**
```bash
./mcp add memory @modelcontextprotocol/server-memory --source npm --category "Memory"
# Tools: create_entities, create_relations, add_observations, delete_entities
```

### **Sequential Thinking**
```bash
./mcp add thinking @modelcontextprotocol/server-sequential-thinking --source npm --category "AI"
# Tools: sequential reasoning and problem solving
```

### **Browser Automation**
```bash
./mcp add puppeteer puppeteer-mcp-server --source npm --category "Automation"
# Tools: browser automation, web scraping, screenshots
```

### **PostgreSQL Database**
```bash
./mcp add postgres enhanced-postgres-mcp-server --source npm --category "Database"
# Tools: query, insert, update, delete operations
```

## 🔧 NPM Package Management

The CLI handles npm packages seamlessly:

### **Explicit NPM Installation**
```bash
./mcp add my-server @company/mcp-server --source npm
# MUST use --source npm flag for npm packages
```

### **Version Management**
```bash
# Install specific version
./mcp add my-server @company/mcp-server@1.2.3 --source npm

# Check installed version
./mcp inspect my-server
# Shows: Version: 1.2.3
```

### **Binary Detection**
```bash
# Automatic binary name inference:
# @modelcontextprotocol/server-memory → mcp-server-memory
# @company/package → package
# regular-package → regular-package
```

## 📊 Monitoring NPM Servers

### **Registry Overview**
```bash
# Check all servers including npm packages
./mcp status

# List with package info
./mcp list

# Focus on npm servers
./mcp list --provider npm
```

### **Server Details**
```bash
# Search for npm packages
./mcp search "modelcontextprotocol"
./mcp search "memory"

# Detailed package inspection
./mcp inspect memory
```

## 🚀 CI/CD Integration

Perfect for testing npm-published MCP servers:

### **Pipeline Example**
```bash
#!/bin/bash
# ci-test-npm-servers.sh

# Add npm MCP servers to test
./mcp add memory @modelcontextprotocol/server-memory --source npm --category "Memory"
./mcp add fs @modelcontextprotocol/server-filesystem --source npm --category "Storage"
./mcp add thinking @modelcontextprotocol/server-sequential-thinking --source npm --category "AI"

# Discover all packages and generate mocks
./mcp sync

# Run comprehensive tests
./mcp test --all

# Check for any failures
if ./mcp status | grep -q "Failed"; then
    echo "❌ Some npm server tests failed"
    exit 1
else
    echo "✅ All npm server tests passed"
fi
```

### **Batch Operations**
```bash
# Add multiple npm servers
./mcp add memory @modelcontextprotocol/server-memory --source npm --category "Memory"
./mcp add fs @modelcontextprotocol/server-filesystem --source npm --category "Storage"
./mcp add db enhanced-postgres-mcp-server --source npm --category "Database"

# Discover and generate all at once
./mcp sync

# Test all npm servers
./mcp test --all
```

## 🔍 Troubleshooting

### **Common Issues**

**npm not found**
```bash
# Install Node.js and npm
brew install node  # macOS
apt install nodejs npm  # Ubuntu

# Check npm installation
npm --version
```

**Package installation fails**
```bash
# Check package exists
npm search @modelcontextprotocol/server-memory

# Try manual installation
npm install -g @modelcontextprotocol/server-memory

# Check global bin directory
npm config get prefix
```

**Binary not found after installation**
```bash
# Check PATH includes npm global bin
echo $PATH

# Add npm global bin to PATH
export PATH="$(npm config get prefix)/bin:$PATH"

# Or use npm-global directory
npm config set prefix '~/.npm-global'
export PATH="~/.npm-global/bin:$PATH"
```

**Discovery Failures**
```bash
# Check binary exists and is executable
which mcp-server-memory
mcp-server-memory --help

# Re-run discovery
./mcp discover memory

# Check discovery output
./mcp inspect memory
```

**Generation Issues**
```bash
# Force regeneration
./mcp generate memory --force

# Check generated files
ls mcp_registry/servers/memory/generated/
```

### **Status Checking**
```bash
# Overall health
./mcp status

# Specific npm server status
./mcp inspect memory

# List all with npm package info
./mcp list
```

## 🎯 Key Benefits

- **Package Management**: Leverages npm's robust package ecosystem
- **Version Tracking**: Automatic version capture from npm registry
- **Binary Detection**: Smart binary name inference and PATH resolution
- **Safe Testing**: Mock servers with no side effects or external dependencies
- **Auto-Discovery**: Automatically detects capabilities from installed binaries
- **CI/CD Ready**: Registry management with health monitoring and batch operations
- **Developer Friendly**: Uses familiar npm package names and versions

## 📦 Directory Structure

After installing an npm MCP server:
```
mcp_registry/servers/memory/
├── config.json           # Server configuration with npm package info
├── discovery.json        # Discovered tools and capabilities
└── generated/            # Generated mock server files
    ├── server.py         # Mock MCP server
    ├── tools.py          # Mock tool implementations
    └── evaluations.json  # Test evaluations
```

**config.json structure:**
```json
{
  "source": {
    "type": "npm",
    "package_name": "@modelcontextprotocol/server-memory",
    "package_version": "2025.9.25",
    "binary_path": "/usr/local/bin/mcp-server-memory",
    "transport": "stdio"
  },
  "metadata": {
    "provider": "npm",
    "category": "Memory"
  }
}
```

---

**Next Steps**: Try installing your favorite npm MCP server and see the magic happen! 🚀