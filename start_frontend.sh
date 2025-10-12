#!/bin/bash
# Start the React frontend

cd "$(dirname "$0")/chat-frontend"

echo "🎨 Starting MCP Chat Frontend..."
echo ""

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies (first time only)..."
    npm install
    echo ""
fi

echo "🌐 Frontend will run on http://localhost:3000"
echo "🔗 Make sure backend is running on http://localhost:5001"
echo ""
echo "Press Ctrl+C to stop"
echo ""

npm start

