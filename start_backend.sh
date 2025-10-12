#!/bin/bash
# Start the chat backend

cd "$(dirname "$0")"

echo "🚀 Starting MCP Chat Backend..."
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found!"
    echo ""
    echo "Please create a .env file with your OpenAI API key:"
    echo "  echo 'OPENAI_API_KEY=sk-your-key-here' > .env"
    echo ""
    exit 1
fi

echo "✅ Found .env file"
echo "📡 Connecting to MCP server..."
echo "🌐 Backend will run on http://localhost:5001"
echo ""

uv run python chat_backend.py

