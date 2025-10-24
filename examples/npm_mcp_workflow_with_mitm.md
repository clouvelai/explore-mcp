# NPM MCP Server Workflow with MITM Interception

## Complete Architecture Flow

```
┌─────────────────┐    ./mcp add    ┌─────────────────┐    npm install    ┌─────────────────┐
│ MCP Registry    │ ──────────────→ │ NPM Package     │ ──────────────→   │ Local Binary    │
│ Entry Created   │                 │ @mcp/server-fs  │                   │ ~/.npm/bin/     │
└─────────────────┘                 └─────────────────┘                   └─────────────────┘
         │                                                                          │
         ▼                    ./mcp run fs --capture-session                       │
┌─────────────────┐                          │                                     │
│ config.json     │                          ▼                                     │
│ discovery.json  │             ┌─────────────────────────────┐                   │
│ sessions/       │ ◄─────────── │ Interactive MCP Client      │ ──────────────────┤
│   session_      │              │                             │                   │
│   2023*.jsonl   │              │ • MITM interceptor enabled  │                   ▼
│ generated/      │              │ • User commands: call, quit │         ┌─────────────────┐
└─────────────────┘              │ • Real-time logging         │         │ Running Server  │
                                 └─────────────────────────────┘         │ stdio transport │
                                              │                          │ + directories   │
                                              ▼                          │ allowed         │
                Real User Sessions: read_file, list_directory, write_file  └─────────────────┘
                              │
                              ▼
                 ./mcp generate fs --use-real-sessions
                      │
                      ▼
        ┌─────────────────────────────────────┐
        │ AI Generation with Real Session Data │
        │ • Authentic request patterns         │
        │ • Realistic response examples        │
        │ • Natural usage flows               │
        └─────────────────────────────────────┘
```

## Core MITM Features

- **Transparent Proxy** - Zero code changes to existing MCP workflows
- **Real Server Communication** - Actual npm server process, not mocks  
- **Complete Logging** - All requests/responses with timestamps
- **Registry Integration** - Logs stored alongside discovery.json and config.json

## Working Example

```bash
# 1. Add npm server to registry
./mcp add fs @modelcontextprotocol/server-filesystem --source npm --category Storage

# 2. Enhanced: Interactive session with capture
./mcp run fs --capture-session
# Opens interactive shell, use the server naturally:
# fs> call read_file README.md
# fs> call list_directory .
# fs> call write_file {"path": "/private/tmp/test.txt", "content": "Hello World"}
# fs> quit

# 3. Generate using real session data
./mcp generate fs --use-real-sessions
# Uses captured interactions for realistic mock responses
```

## Key Benefits

- **Zero Modification** - Works with any existing npm MCP server
- **Real Operations** - Captures actual server behavior, not mocks
- **Complete Audit Trail** - Every request/response logged with timestamps  
- **Registry Integration** - Logs stored alongside discovery.json and config.json
- **Debug Visibility** - See exact communication flow for troubleshooting

## Real Session Data Example

```bash
# Sessions automatically saved to registry
ls mcp_registry/servers/filesystem/sessions/
# session_20251023_230251.jsonl

# Each session contains complete request/response flows
```

```json
{"type": "request", "timestamp": "2025-10-23T23:02:51.251537", "count": 1, "method": "initialize", "args": [], "kwargs": {}}
{"type": "response", "timestamp": "2025-10-23T23:02:51.387728", "count": 1, "method": "initialize", "result": {"_type": "InitializeResult", "meta": null, "protocolVersion": "2025-06-18", "capabilities": {"_type": "ServerCapabilities", "experimental": null, "logging": null, "prompts": null, "resources": null, "tools": {"_type": "ToolsCapability", "listChanged": null}, "completions": null}, "serverInfo": {"_type": "Implementation", "name": "secure-filesystem-server", "title": null, "version": "0.2.0", "websiteUrl": null, "icons": null}, "instructions": null}, "error": null}
{"type": "request", "timestamp": "2025-10-23T23:02:51.387901", "count": 2, "method": "list_tools", "args": [], "kwargs": {}}
{"type": "response", "timestamp": "2025-10-23T23:02:51.393048", "count": 2, "method": "list_tools", "result": {"_type": "ListToolsResult", "meta": null, "nextCursor": null, "tools": [{"_type": "Tool", "name": "read_file", "title": null, "description": "Read the complete contents of a file as text. DEPRECATED: Use read_text_file instead.", "inputSchema": {"type": "object", "properties": {"path": {"type": "string"}, "tail": {"type": "number", "description": "If provided, returns only the last N lines of the file"}, "head": {"type": "number", "description": "If provided, returns only the first N lines of the file"}}, "required": ["path"], "additionalProperties": false, "$schema": "http://json-schema.org/draft-07/schema#"}, "outputSchema": null, "icons": null, "annotations": null, "meta": null}, {"_type": "Tool", "name": "read_text_file", "title": null, "description": "Read the complete contents of a file from the file system as text. Handles various text encodings and provides detailed error messages if the file cannot be read. Use this tool when you need to examine the contents of a single file. Use the 'head' parameter to read only the first N lines of a file, or the 'tail' parameter to read only the last N lines of a file. Operates on the file as text regardless of extension. Only works within allowed directories.", "inputSchema": {"type": "object", "properties": {"path": {"type": "string"}, "tail": {"type": "number", "description": "If provided, returns only the last N lines of the file"}, "head": {"type": "number", "description": "If provided, returns only the first N lines of the file"}}, "required": ["path"], "additionalProperties": false, "$schema": "http://json-schema.org/draft-07/schema#"}, "outputSchema": null, "icons": null, "annotations": null, "meta": null}, {"_type": "Tool", "name": "read_media_file", "title": null, "description": "Read an image or audio file. Returns the base64 encoded data and MIME type. Only works within allowed directories.", "inputSchema": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"], "additionalProperties": false, "$schema": "http://json-schema.org/draft-07/schema#"}, "outputSchema": null, "icons": null, "annotations": null, "meta": null}, {"_type": "Tool", "name": "read_multiple_files", "title": null, "description": "Read the contents of multiple files simultaneously. This is more efficient than reading files one by one when you need to analyze or compare multiple files. Each file's content is returned with its path as a reference. Failed reads for individual files won't stop the entire operation. Only works within allowed directories.", "inputSchema": {"type": "object", "properties": {"paths": {"type": "array", "items": {"type": "string"}}}, "required": ["paths"], "additionalProperties": false, "$schema": "http://json-schema.org/draft-07/schema#"}, "outputSchema": null, "icons": null, "annotations": null, "meta": null}, {"_type": "Tool", "name": "write_file", "title": null, "description": "Create a new file or completely overwrite an existing file with new content. Use with caution as it will overwrite existing files without warning. Handles text content with proper encoding. Only works within allowed directories.", "inputSchema": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"], "additionalProperties": false, "$schema": "http://json-schema.org/draft-07/schema#"}, "outputSchema": null, "icons": null, "annotations": null, "meta": null}, {"_type": "Tool", "name": "edit_file", "title": null, "description": "Make line-based edits to a text file. Each edit replaces exact line sequences with new content. Returns a git-style diff showing the changes made. Only works within allowed directories.", "inputSchema": {"type": "object", "properties": {"path": {"type": "string"}, "edits": {"type": "array", "items": {"type": "object", "properties": {"oldText": {"type": "string", "description": "Text to search for - must match exactly"}, "newText": {"type": "string", "description": "Text to replace with"}}, "required": ["oldText", "newText"], "additionalProperties": false}}, "dryRun": {"type": "boolean", "default": false, "description": "Preview changes using git-style diff format"}}, "required": ["path", "edits"], "additionalProperties": false, "$schema": "http://json-schema.org/draft-07/schema#"}, "outputSchema": null, "icons": null, "annotations": null, "meta": null}, {"_type": "Tool", "name": "create_directory", "title": null, "description": "Create a new directory or ensure a directory exists. Can create multiple nested directories in one operation. If the directory already exists, this operation will succeed silently. Perfect for setting up directory structures for projects or ensuring required paths exist. Only works within allowed directories.", "inputSchema": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"], "additionalProperties": false, "$schema": "http://json-schema.org/draft-07/schema#"}, "outputSchema": null, "icons": null, "annotations": null, "meta": null}, {"_type": "Tool", "name": "list_directory", "title": null, "description": "Get a detailed listing of all files and directories in a specified path. Results clearly distinguish between files and directories with [FILE] and [DIR] prefixes. This tool is essential for understanding directory structure and finding specific files within a directory. Only works within allowed directories.", "inputSchema": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"], "additionalProperties": false, "$schema": "http://json-schema.org/draft-07/schema#"}, "outputSchema": null, "icons": null, "annotations": null, "meta": null}, {"_type": "Tool", "name": "list_directory_with_sizes", "title": null, "description": "Get a detailed listing of all files and directories in a specified path, including sizes. Results clearly distinguish between files and directories with [FILE] and [DIR] prefixes. This tool is useful for understanding directory structure and finding specific files within a directory. Only works within allowed directories.", "inputSchema": {"type": "object", "properties": {"path": {"type": "string"}, "sortBy": {"type": "string", "enum": ["name", "size"], "default": "name", "description": "Sort entries by name or size"}}, "required": ["path"], "additionalProperties": false, "$schema": "http://json-schema.org/draft-07/schema#"}, "outputSchema": null, "icons": null, "annotations": null, "meta": null}, {"_type": "Tool", "name": "directory_tree", "title": null, "description": "Get a recursive tree view of files and directories as a JSON structure. Each entry includes 'name', 'type' (file/directory), and 'children' for directories. Files have no children array, while directories always have a children array (which may be empty). The output is formatted with 2-space indentation for readability. Only works within allowed directories.", "inputSchema": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"], "additionalProperties": false, "$schema": "http://json-schema.org/draft-07/schema#"}, "outputSchema": null, "icons": null, "annotations": null, "meta": null}, {"_type": "Tool", "name": "move_file", "title": null, "description": "Move or rename files and directories. Can move files between directories and rename them in a single operation. If the destination exists, the operation will fail. Works across different directories and can be used for simple renaming within the same directory. Both source and destination must be within allowed directories.", "inputSchema": {"type": "object", "properties": {"source": {"type": "string"}, "destination": {"type": "string"}}, "required": ["source", "destination"], "additionalProperties": false, "$schema": "http://json-schema.org/draft-07/schema#"}, "outputSchema": null, "icons": null, "annotations": null, "meta": null}, {"_type": "Tool", "name": "search_files", "title": null, "description": "Recursively search for files and directories matching a pattern. Searches through all subdirectories from the starting path. The search is case-insensitive and matches partial names. Returns full paths to all matching items. Great for finding files when you don't know their exact location. Only searches within allowed directories.", "inputSchema": {"type": "object", "properties": {"path": {"type": "string"}, "pattern": {"type": "string"}, "excludePatterns": {"type": "array", "items": {"type": "string"}, "default": []}}, "required": ["path", "pattern"], "additionalProperties": false, "$schema": "http://json-schema.org/draft-07/schema#"}, "outputSchema": null, "icons": null, "annotations": null, "meta": null}, {"_type": "Tool", "name": "get_file_info", "title": null, "description": "Retrieve detailed metadata about a file or directory. Returns comprehensive information including size, creation time, last modified time, permissions, and type. This tool is perfect for understanding file characteristics without reading the actual content. Only works within allowed directories.", "inputSchema": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"], "additionalProperties": false, "$schema": "http://json-schema.org/draft-07/schema#"}, "outputSchema": null, "icons": null, "annotations": null, "meta": null}, {"_type": "Tool", "name": "list_allowed_directories", "title": null, "description": "Returns the list of directories that this server is allowed to access. Subdirectories within these allowed directories are also accessible. Use this to understand which directories and their nested paths are available before trying to access files.", "inputSchema": {"type": "object", "properties": {}, "required": []}, "outputSchema": null, "icons": null, "annotations": null, "meta": null}]}, "error": null}
{"type": "request", "timestamp": "2025-10-23T23:02:51.393485", "count": 3, "method": "call_tool", "args": ["read_file", {"path": "README.md"}], "kwargs": {}}
{"type": "response", "timestamp": "2025-10-23T23:02:51.395592", "count": 3, "method": "call_tool", "result": {"_type": "CallToolResult", "meta": null, "content": [{"_type": "TextContent", "type": "text", "text": "# MCP CI/CD Automation Platform\n\n**AI-powered mock server generation and testing for MCP servers**\n\nAutomatically generates safe, side-effect-free test environments from any MCP server implementation using Claude AI..."}], "structuredContent": null, "isError": false}, "error": null}
{"type": "request", "timestamp": "2025-10-23T23:02:51.395840", "count": 4, "method": "call_tool", "args": ["list_directory", {"path": "."}], "kwargs": {}}
{"type": "response", "timestamp": "2025-10-23T23:02:51.396556", "count": 4, "method": "call_tool", "result": {"_type": "CallToolResult", "meta": null, "content": [{"_type": "TextContent", "type": "text", "text": "[DIR] .claude\n[FILE] .env\n[DIR] .git\n[FILE] .gitignore\n[FILE] .isort.cfg\n[DIR] .mcp-ci\n[DIR] .mcp_data\n[DIR] .pytest_cache\n[DIR] .venv\n[FILE] CLAUDE.md\n[FILE] ENV_TEMPLATE\n[FILE] QUICKSTART.md\n[FILE] README.md\n[FILE] TEST_GUIDE.md\n[DIR] ai_generation\n[DIR] backend\n[DIR] chat-frontend\n[FILE] client.py\n[FILE] demo_session.txt\n[DIR] demos\n[DIR] development_notes\n[DIR] examples\n[DIR] generated\n[FILE] intercept_filesystem_server.py\n[FILE] main.py\n[FILE] mcp\n[FILE] mcp_cli.py\n[DIR] mcp_interceptor\n[DIR] mcp_registry\n[DIR] mcp_servers\n[FILE] pyproject.toml\n[FILE] pytest.ini\n[FILE] run_tests.sh\n[FILE] start_backend.sh\n[FILE] start_frontend.sh\n[DIR] tests\n[DIR] utils\n[FILE] uv.lock"}], "structuredContent": null, "isError": false}, "error": null}
{"type": "request", "timestamp": "2025-10-23T23:02:51.396678", "count": 5, "method": "call_tool", "args": ["write_file", {"path": "/private/tmp/demo.txt", "content": "Demo from npm workflow"}], "kwargs": {}}
{"type": "response", "timestamp": "2025-10-23T23:02:51.399087", "count": 5, "method": "call_tool", "result": {"_type": "CallToolResult", "meta": null, "content": [{"_type": "TextContent", "type": "text", "text": "Successfully wrote to /private/tmp/demo.txt"}], "structuredContent": null, "isError": false}, "error": null}
```

**Benefits for AI Generation:**
- **Real Usage Patterns** - Authentic tool call sequences 
- **Actual Response Data** - Real file contents, directory listings, error messages
- **Natural Workflows** - How users actually interact with the server
- **Better Mock Responses** - AI generates realistic responses based on real data

This transforms npm MCP server management into a comprehensive platform for capturing real-world usage to improve AI generation quality.