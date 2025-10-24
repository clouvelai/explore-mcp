# MCP Registry Examples

This directory contains working examples demonstrating various features of the MCP Registry.

## Available Examples

### 📦 [NPM Filesystem Example](./npm-filesystem-example/)
Complete example showing how to install and use npm-published MCP servers.

- **Package**: `@modelcontextprotocol/server-filesystem`
- **Features**: File operations (read, write, list, delete)
- **Includes**: CLI usage, Python API, complete workflow

**Quick Start:**
```bash
# Run the complete example
./examples/npm-filesystem-example/run-example.sh

# Or run Python example
python3 examples/npm-filesystem-example/python-example.py
```

## Example Structure

Each example includes:
- 📖 **README.md**: Complete documentation
- 🚀 **run-example.sh**: Automated script to run the example
- 🐍 **python-example.py**: Programmatic usage demonstration
- 📝 **Expected outputs and troubleshooting**

## Prerequisites

- Python 3.8+
- Node.js and npm (for npm examples)
- MCP Registry installed and `./mcp` CLI available

## Running Examples

From the project root:

```bash
# Make sure you're in the right directory
pwd  # Should show: /path/to/explore-mcp

# Run an example
./examples/npm-filesystem-example/run-example.sh
```

## Example Output

All examples show:
- ✅ Installation progress
- 🔍 Discovery results  
- 🏗️ Mock generation
- 📋 Server inspection
- 📁 Generated file locations

## Contributing Examples

To add a new example:

1. Create directory: `examples/your-example-name/`
2. Add `README.md` with complete documentation
3. Add `run-example.sh` for automated execution
4. Add `python-example.py` for programmatic usage
5. Update this main README

## Troubleshooting

### Common Issues

**npm command not found:**
```bash
# Install Node.js
brew install node  # macOS
apt install nodejs npm  # Ubuntu
```

**Permission errors:**
```bash
# Fix npm permissions
npm config set prefix '~/.npm-global'
export PATH="~/.npm-global/bin:$PATH"
```

**Python import errors:**
```bash
# Make sure you're in project root
cd /path/to/explore-mcp
python3 examples/npm-filesystem-example/python-example.py
```