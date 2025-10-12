# Testing Your MCP Chat Interface

## Prerequisites Checklist

- [ ] OpenAI API key (get from https://platform.openai.com/api-keys)
- [ ] Node.js installed (`node --version`)
- [ ] Python environment ready (`uv` installed)

## Quick Start (3 Steps)

### 1️⃣ Set Your API Key (30 seconds)

```bash
cd /Users/samuelclark/Desktop/explore-mcp
echo "OPENAI_API_KEY=sk-your-actual-key" > .env
# ⚠️ Replace sk-your-actual-key with your real OpenAI API key!
```

### 2️⃣ Start Backend (Terminal 1)

```bash
cd /Users/samuelclark/Desktop/explore-mcp
./start_backend.sh

# Or manually:
# uv run python chat_backend.py
```

Wait for: `Backend running on http://localhost:5001`

### 3️⃣ Start Frontend (Terminal 2)

```bash
cd /Users/samuelclark/Desktop/explore-mcp
./start_frontend.sh

# Or manually:
# cd chat-frontend
# npm install && npm start
```

Browser will open automatically at http://localhost:3000

## 🧪 Test Cases

Once the chat interface loads, try these:

### Test 1: Simple Addition
```
You: What's 25 + 17?
Expected: GPT-4 uses sum tool, responds with "42"
```

### Test 2: Natural Language
```
You: I have 100 apples and get 50 more. How many total?
Expected: GPT-4 uses sum tool with 100 and 50
```

### Test 3: Multiple Calculations
```
You: What's 10 + 5, and then what's 7 + 8?
Expected: GPT-4 uses sum tool twice
```

### Test 4: Non-Math Question (should NOT use tool)
```
You: What is the capital of France?
Expected: GPT-4 answers directly without using sum tool
```

### Test 5: Edge Cases
```
You: Add -5 and 15
Expected: sum tool returns 10

You: What's 3.14 + 2.86?
Expected: sum tool handles decimals, returns 6.0
```

## 🔍 What to Look For

### In the Chat UI:
- ✅ Message appears in chat
- ✅ "Typing..." indicator shows
- ✅ Response appears from assistant
- ✅ Tool badge shows (e.g., "🔧 sum")
- ✅ Tool result displays (e.g., "The sum of 25 and 17 is 42")

### In Backend Terminal:
```
INFO: "POST /api/chat HTTP/1.1" 200 OK
```

### In Browser Console (F12):
```
No CORS errors
No network errors
```

## 🐛 Troubleshooting

### Backend Won't Start

**Error: "OPENAI_API_KEY not found"**
```bash
# Check if .env exists
ls -la .env

# If not, create it:
echo "OPENAI_API_KEY=sk-your-key" > .env
```

**Error: "Address already in use"**
```bash
# Kill process on port 5001
lsof -ti:5001 | xargs kill -9
```

### Frontend Won't Start

**Error: "npm command not found"**
- Install Node.js from https://nodejs.org/

**Error: "Failed to compile"**
```bash
cd chat-frontend
rm -rf node_modules package-lock.json
npm install
```

### No Response from GPT-4

**Error: "Connection refused"**
- Make sure backend is running on port 5001

**Error: "Invalid API key"**
- Check your OpenAI API key in .env
- Make sure it starts with `sk-`

**Error: "Rate limit exceeded"**
- Wait a few minutes
- Check your OpenAI usage limits

## 📊 Understanding the Flow

```
1. You type: "What's 5 + 3?"
   ↓
2. React → POST /api/chat
   ↓
3. Backend → OpenAI: "Here's what I can do: [sum tool]"
   ↓
4. OpenAI: "I need to call sum(5, 3)"
   ↓
5. Backend → MCP Server: call_tool("sum", {a:5, b:3})
   ↓
6. MCP Server executes: @mcp.tool() def sum(a, b)
   ↓
7. Result: "The sum of 5 and 3 is 8"
   ↓
8. Backend → OpenAI: "Tool returned: 8"
   ↓
9. OpenAI: "The answer is 8!"
   ↓
10. Backend → React: Display response
```

## 🎯 Success Criteria

Your chat is working correctly if:

- ✅ Messages send and receive
- ✅ GPT-4 automatically uses sum tool for math
- ✅ Tool badge appears showing tool was used
- ✅ Tool result is displayed
- ✅ Final answer is natural and correct
- ✅ No errors in console

## 🚀 Next Steps After Testing

Once it works:

1. **Add more tools** to `server.py`:
   ```python
   @mcp.tool()
   def multiply(a: float, b: float) -> str:
       return f"The product is {a * b}"
   ```

2. **Customize the UI** in `chat-frontend/src/App.css`

3. **Add conversation persistence** (save to database)

4. **Deploy it** (Vercel for frontend, Railway for backend)

## 📝 Stopping the Services

```bash
# In both terminals (backend and frontend):
Press Ctrl+C

# Or kill by port:
lsof -ti:5001 | xargs kill -9  # Backend
lsof -ti:3000 | xargs kill -9  # Frontend
```

## 💡 Pro Tips

1. Keep both terminal windows visible to see logs
2. Open browser console (F12) to debug issues
3. Use the "Clear Chat" button to reset conversation
4. Check `conversation_history` in backend for debugging
5. Test with small inputs first before complex queries

Happy testing! 🎉

