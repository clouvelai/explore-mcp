# Quick Start Guide - 5 Minutes to Chat!

Get your MCP chat interface running in 5 minutes.

## Prerequisites Check

```bash
# Check Python (should be 3.10+)
python --version

# Check Node.js (should be 16+)
node --version

# If Node.js is missing, install from: https://nodejs.org/
```

## Quick Setup (Copy & Paste)

### Step 1: Set Your OpenAI API Key (30 seconds)

```bash
cd /Users/samuelclark/Desktop/explore-mcp

# Create .env file with your API key
echo "OPENAI_API_KEY=sk-your-actual-key-here" > .env

# ⚠️ Edit .env and replace sk-your-actual-key-here with your real key!
# Get one at: https://platform.openai.com/api-keys
```

### Step 2: Start Backend (1 minute)

```bash
# Terminal 1 - Start the Flask backend
cd /Users/samuelclark/Desktop/explore-mcp
uv run python chat_backend.py

# Wait for: "Backend running on http://localhost:5001"
```

### Step 3: Start Frontend (2 minutes)

```bash
# Terminal 2 - Start the React frontend
cd /Users/samuelclark/Desktop/explore-mcp/chat-frontend
npm install && npm start

# This will open http://localhost:3000 in your browser
```

## You're Done! 🎉

The chat interface should open automatically. Try:

- "What's 25 + 17?"
- "Add 100 and 42"
- "Calculate the sum of 33 and 66"

Watch GPT-4 automatically use your MCP server's `sum` tool!

## What's Happening?

```
You → React UI → Flask Backend → OpenAI GPT-4
                       ↓
                  MCP Server (sum tool)
                       ↓
                   Result back through chain
```

## Need Help?

See detailed guide: [CHAT_SETUP.md](development_notes/CHAT_SETUP.md)

## Common Issues

**"OPENAI_API_KEY not found"**
- Make sure `.env` file exists in `/Users/samuelclark/Desktop/explore-mcp/`
- Check that the API key starts with `sk-`

**"npm command not found"**
- Install Node.js from https://nodejs.org/

**Port already in use**
- Backend: Change port in `chat_backend.py` (line with `port=5001`)
- Frontend: Kill other processes on port 3000

## Stop Everything

Press `Ctrl+C` in both terminals (backend and frontend).

