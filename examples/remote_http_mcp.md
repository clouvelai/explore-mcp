# Remote HTTP MCP Server Workflow

This guide shows how to add, discover, and test remote HTTP MCP servers using the unified MCP CLI.

## 🌐 Complete Remote HTTP MCP Server Workflow

### **🚀 Quick Start (Recommended)**
```bash
# One command to add + discover + generate
./mcp add my-api https://api.example.com/mcp --category "External API"
./mcp sync  # Discovers all new servers and generates mocks
./mcp test my-api
```

### **📋 Step-by-Step Workflow**

**1. Add Remote Server**
```bash
./mcp add external-docs https://docs.example.com/api/mcp \
  --category "Documentation" \
  --description "External documentation API"
```
- ✅ **Auto-detects HTTP transport** from URL
- ✅ **Registers server** in registry with metadata
- ✅ **Creates directory structure** in `mcp_registry/servers/external-docs/`

**2. Inspect Configuration**
```bash
./mcp inspect external-docs
```
Shows:
- Server metadata (name, category, provider)
- Source configuration (URL, transport)
- Discovery/generation settings

**3. Discover API Capabilities**
```bash
./mcp discover external-docs
```
- 🌐 **Connects to remote server** via HTTP
- 📡 **Discovers tools, resources, prompts** 
- 💾 **Saves discovery.json** with full API schema
- 🔐 **Tracks content hash** for change detection

**4. Generate Mock Server**
```bash
./mcp generate external-docs
```
- 🤖 **AI generates realistic mock responses** using Claude
- 📝 **Creates mock server** (`generated/server.py`)
- 🧪 **Creates test suite** (`generated/evaluations.json`)

**5. Test Mock Server**
```bash
./mcp test external-docs
```
- 🔬 **Runs evaluation suite** against generated mock
- ✅ **Validates tool calls** and response formats
- 📊 **Reports pass/fail results**

## 🎯 Real Example: Microsoft Learn API

Here's a complete example using Microsoft's public MCP server:

```bash
# Add Microsoft Learn documentation API
./mcp add ms-docs https://learn.microsoft.com/api/mcp \
  --category "Documentation" \
  --description "Microsoft Learn documentation API"

# Expected output:
# ✅ Added server 'ms-docs' to registry
#    Source: https://learn.microsoft.com/api/mcp
#    Category: Documentation
#    Provider: Remote

# Inspect the configuration
./mcp inspect ms-docs

# Expected output:
# 📋 Server: ms-docs
# ==================================================
# Name: ms-docs
# Description: Microsoft Learn documentation API
# Category: Documentation
# Provider: Remote
# Version: 1.0.0
# 
# 📍 Source:
# Type: remote
# URL: https://learn.microsoft.com/api/mcp
# Transport: stdio

# Discover capabilities
./mcp discover ms-docs

# Expected output:
# 📡 Discovering server 'ms-docs'...
# 🌐 HTTP server URL detected: https://learn.microsoft.com/api/mcp
# ✓ Found 3 tools
# ✓ Found 0 resources
# ✓ Found 0 prompts
# ✅ Discovery completed for 'ms-docs'

# Generate mock server
./mcp generate ms-docs

# Expected output:
# 🔨 Generating mocks for server 'ms-docs'...
# 🤖 Generating AI-powered mock responses...
# ✅ Generated tools.py with 3 tools
# ✅ Generated server.py
# ✅ Generation completed for 'ms-docs'

# Test the mock
./mcp test ms-docs

# Check status
./mcp status

# Expected output:
# 📊 MCP Registry Status
# ==================================================
# Total servers: 6
# Discovered: 4/6
# Generated: 4/6
# 
# 📂 By Category:
#   Documentation: 2
#   ...

# Clean up (optional)
./mcp remove ms-docs
```

## 🔧 Transport Options

The CLI auto-detects transport from URLs, but you can override:

### **HTTP (Default for https:// URLs)**
```bash
./mcp add api-server https://api.example.com/mcp
# Auto-detects HTTP transport
```

### **Server-Sent Events**
```bash
./mcp add realtime-api https://api.example.com/sse --transport sse
# Useful for streaming/realtime APIs
```

### **Explicit HTTP Specification**
```bash
./mcp add custom-api http://localhost:8080/mcp --transport http
# Force HTTP even for non-standard URLs
```

## 📊 Monitoring Remote Servers

### **Registry Overview**
```bash
# Check all servers including remote
./mcp status

# List with status indicators
./mcp list

# Focus on specific categories
./mcp list --category "External API"
./mcp list --category "Documentation"
```

### **Server Details**
```bash
# Search for servers
./mcp search "microsoft"
./mcp search "docs"

# Detailed inspection
./mcp inspect external-docs
```

## 🚀 CI/CD Integration

Perfect for testing external APIs without side effects:

### **Pipeline Example**
```bash
#!/bin/bash
# ci-test-external-apis.sh

# Add external APIs to test
./mcp add partner-api https://api.partner.com/mcp --category "External"
./mcp add docs-api https://docs.service.com/mcp --category "Documentation"

# Discover all APIs and generate mocks
./mcp sync

# Run comprehensive tests
./mcp test --all

# Check for any failures
if ./mcp status | grep -q "Failed"; then
    echo "❌ Some external API tests failed"
    exit 1
else
    echo "✅ All external API tests passed"
fi
```

### **Batch Operations**
```bash
# Add multiple remote servers
./mcp add auth-api https://auth.example.com/mcp --category "Authentication"
./mcp add billing-api https://billing.example.com/mcp --category "Billing"
./mcp add metrics-api https://metrics.example.com/mcp --category "Analytics"

# Discover and generate all at once
./mcp sync

# Test all external APIs
./mcp test --all
```

## 🔍 Troubleshooting

### **Common Issues**

**Connection Errors**
```bash
# Check if the server is accessible
curl https://api.example.com/mcp

# Try explicit transport specification
./mcp add my-api https://api.example.com/mcp --transport http
```

**Discovery Failures**
```bash
# Re-run discovery with fresh attempt
./mcp discover my-api

# Check discovery output
./mcp inspect my-api
```

**Generation Issues**
```bash
# Force regeneration
./mcp generate my-api --force

# Check generated files
ls mcp_registry/servers/my-api/generated/
```

### **Status Checking**
```bash
# Overall health
./mcp status

# Specific server status
./mcp inspect my-api

# List all with status
./mcp list
```

## 🎯 Key Benefits

- **Safe Testing**: Mock servers with no side effects or external dependencies
- **Auto-Discovery**: Automatically detects transport protocols and API schemas
- **Change Detection**: MD5 hash tracking for API version changes
- **CI/CD Ready**: Registry management with health monitoring and batch operations
- **Developer Friendly**: npm/docker-style commands developers already know

---

**Next Steps**: Try adding your own remote MCP server and see the magic happen! 🚀