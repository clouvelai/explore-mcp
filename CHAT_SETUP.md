# MCP Chat Interface Setup Guide

A beautiful chat interface that connects OpenAI's GPT-4 to your MCP server, demonstrating how AI assistants can use MCP tools!

## Architecture

```
┌─────────────────┐         ┌──────────────────┐         ┌─────────────────┐
│  React Frontend │ ◄────► │  Flask Backend   │ ◄────► │   MCP Server    │
│   (Port 3000)   │  HTTP  │   (Port 5001)    │  stdio │   (server.py)   │
│                 │         │                  │         │                 │
│  User types     │         │  Manages OpenAI  │         │  Executes tools │
│  messages       │         │  + MCP bridge    │         │  (sum function) │
└─────────────────┘         └──────────────────┘         └─────────────────┘
```

## Prerequisites

1. **Python 3.10+** (already installed)
2. **Node.js 16+** - for React frontend
   ```bash
   # Check if installed
   node --version
   npm --version
   ```
3. **OpenAI API Key** - Get one at https://platform.openai.com/api-keys

## Step 1: Set Up Environment Variables

Create a `.env` file in the project root:

```bash
# In /Users/samuelclark/Desktop/explore-mcp/
cat > .env << 'EOF'
OPENAI_API_KEY=your_actual_openai_api_key_here
EOF
```

**Important**: Replace `your_actual_openai_api_key_here` with your real OpenAI API key!

## Step 2: Start the MCP Server

The MCP server needs to be running (it will be auto-started by the backend, but good to test):

```bash
cd /Users/samuelclark/Desktop/explore-mcp
uv run python server.py
```

You should see the FastMCP banner. Press `Ctrl+C` to stop (it will auto-start with backend).

## Step 3: Start the Flask Backend

In a new terminal:

```bash
cd /Users/samuelclark/Desktop/explore-mcp
uv run python chat_backend.py
```

You should see:
```
🚀 Starting chat backend...
📡 Connecting to MCP server on startup...
🌐 Backend running on http://localhost:5001
```

Keep this terminal running!

## Step 4: Start the React Frontend

In a new terminal:

```bash
cd /Users/samuelclark/Desktop/explore-mcp/chat-frontend

# Install dependencies (first time only)
npm install

# Start the development server
npm start
```

This will:
- Install React and dependencies (first time)
- Start the dev server on http://localhost:3000
- Open your browser automatically

## Step 5: Start Chatting! 🎉

The chat interface will open in your browser. Try these examples:

### Example Conversations

**Example 1: Simple Addition**
```
You: What's 25 + 17?
🤖: Let me calculate that for you.
    [Uses sum tool: 25 + 17]
    The sum of 25 and 17 is 42!
```

**Example 2: Word Problem**
```
You: I have 100 apples and my friend gives me 50 more. How many do I have?
🤖: Let me calculate that.
    [Uses sum tool: 100 + 50]
    You now have 150 apples in total!
```

**Example 3: Multiple Calculations**
```
You: What's 10 + 5, and then add 3 to that?
🤖: Let me break this down:
    [Uses sum tool: 10 + 5 = 15]
    [Uses sum tool: 15 + 3 = 18]
    The final result is 18!
```

## How It Works

### 1. **User Sends Message**
   - You type a question in the chat interface
   - Frontend sends it to Flask backend

### 2. **Backend Processes**
   - Flask receives the message
   - Connects to MCP server to discover tools
   - Sends message + tool definitions to OpenAI

### 3. **OpenAI Decides**
   - GPT-4 reads your message
   - Decides if it needs to use a tool
   - Returns either: direct answer OR tool call request

### 4. **Tool Execution (if needed)**
   - Backend receives tool call from OpenAI
   - Executes the tool via MCP server
   - Gets result (e.g., "The sum of 25 and 17 is 42")
   - Sends result back to OpenAI

### 5. **Final Response**
   - OpenAI formulates a natural language response
   - Backend sends it to frontend
   - You see the answer in the chat!

## Project Structure

```
explore-mcp/
├── server.py                 # MCP server with tools
├── chat_backend.py          # Flask backend (OpenAI ↔ MCP bridge)
├── client.py                # Test client (optional)
├── .env                     # API keys (DO NOT COMMIT!)
├── chat-frontend/
│   ├── package.json         # React dependencies
│   ├── public/
│   │   └── index.html       # HTML template
│   └── src/
│       ├── index.js         # React entry point
│       ├── App.js           # Main chat component
│       └── App.css          # Styling
├── README.md                # Main project docs
└── CHAT_SETUP.md           # This file
```

## Troubleshooting

### Backend Issues

**Error: "No module named 'openai'"**
```bash
cd /Users/samuelclark/Desktop/explore-mcp
uv sync
```

**Error: "OPENAI_API_KEY not found"**
- Make sure `.env` file exists in the project root
- Check that it contains `OPENAI_API_KEY=sk-...`
- Restart the backend after creating `.env`

**Error: "Connection refused to MCP server"**
- Make sure `server.py` is in the same directory as `chat_backend.py`
- Check that Python is accessible via `python` command

### Frontend Issues

**Error: "npm command not found"**
- Install Node.js: https://nodejs.org/

**Error: "Failed to compile"**
- Delete `node_modules` and reinstall:
  ```bash
  cd chat-frontend
  rm -rf node_modules package-lock.json
  npm install
  ```

**Error: "Network request failed"**
- Make sure the Flask backend is running on port 5001
- Check browser console (F12) for CORS errors

### API Issues

**Error: "Invalid API key"**
- Verify your OpenAI API key at https://platform.openai.com/api-keys
- Make sure there are no extra spaces in the `.env` file

**Error: "Rate limit exceeded"**
- You've hit OpenAI's rate limit
- Wait a few minutes and try again
- Consider upgrading your OpenAI plan

## Features to Try

### Current Features
- ✅ Real-time chat with GPT-4
- ✅ Automatic tool calling
- ✅ Visual tool execution feedback
- ✅ Conversation history
- ✅ Clear chat button
- ✅ Beautiful gradient UI

### Extend It!

Want to add more capabilities? Edit `server.py`:

```python
@mcp.tool()
def multiply(a: float, b: float) -> str:
    """Multiply two numbers together."""
    result = a * b
    return f"The product of {a} and {b} is {result}"

@mcp.tool()
def divide(a: float, b: float) -> str:
    """Divide one number by another."""
    if b == 0:
        return "Error: Cannot divide by zero"
    result = a / b
    return f"{a} divided by {b} is {result}"
```

Restart the backend, and GPT-4 will automatically use these new tools!

## Cost Considerations

Using OpenAI's API costs money (but it's quite cheap for experimentation):

- **GPT-4o-mini**: ~$0.15 per 1M input tokens, $0.60 per 1M output tokens
- **Typical conversation**: ~$0.001 - $0.01 per message

Set up billing alerts in your OpenAI dashboard to avoid surprises!

## Next Steps

1. **Add More Tools**: Implement multiply, divide, power, etc.
2. **Add Resources**: Expose calculation history via MCP resources
3. **Add Prompts**: Create prompt templates for math tutoring
4. **Improve UI**: Add message timestamps, user avatars, themes
5. **Add Authentication**: Secure the backend with user auth
6. **Deploy**: Host on Vercel (frontend) + Railway (backend)

## Stopping the Application

To stop everything:

1. **Frontend**: Press `Ctrl+C` in the terminal running `npm start`
2. **Backend**: Press `Ctrl+C` in the terminal running `chat_backend.py`
3. **MCP Server**: Auto-stops when backend stops

## Security Notes

⚠️ **Important Security Considerations**:

1. **Never commit `.env` file** - Add it to `.gitignore`
2. **API Key Security** - Don't share your OpenAI API key
3. **CORS in Production** - Configure proper CORS for production
4. **Rate Limiting** - Add rate limiting to prevent abuse
5. **Input Validation** - Validate all user inputs in production

## Resources

- **OpenAI API Docs**: https://platform.openai.com/docs
- **MCP Specification**: https://spec.modelcontextprotocol.io/
- **FastMCP**: https://gofastmcp.com
- **React Docs**: https://react.dev

## Support

If you run into issues:
1. Check the troubleshooting section above
2. Look at terminal output for error messages
3. Check browser console (F12) for frontend errors
4. Review this setup guide carefully

Happy chatting! 🚀

