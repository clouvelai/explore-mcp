# Quick Start: Google Drive MCP Integration

Get your chat app running with Google Drive in 5 minutes!

## Prerequisites

- Python 3.10+
- Node.js 16+
- OpenAI API key
- Google account

## Step 1: Install Dependencies (2 minutes)

```bash
# Install Python dependencies
uv sync

# Install frontend dependencies
cd chat-frontend
npm install
cd ..
```

## Step 2: Set Up Environment (1 minute)

```bash
# Copy environment template
cp ENV_TEMPLATE .env

# Edit .env file and add:
# - Your OpenAI API key
# - A random secret key
# - Google OAuth credentials (see SETUP.md for getting these)
```

**Quick .env example:**
```bash
OPENAI_API_KEY=sk-your-key-here
FLASK_SECRET_KEY=my-super-secret-random-string
GOOGLE_CLIENT_ID=123456789-abc.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-yoursecret
```

## Step 3: Run the App (30 seconds)

### Terminal 1 - Backend
```bash
python chat_backend.py
```

You should see:
```
🚀 Starting chat backend...
📡 Connecting to MCP servers...
🌐 Backend running on http://localhost:5001

📋 Available servers:
  - Calculator: ✅ No auth needed
  - Google Drive: 🔐 Requires auth
```

### Terminal 2 - Frontend
```bash
cd chat-frontend
npm start
```

Browser opens at http://localhost:3000

## Step 4: Connect Google Drive (1 minute)

1. In the web UI, click **"Connect with Google"** on the Google Drive card
2. Sign in with Google in the popup
3. Grant permissions
4. Popup closes automatically
5. Google Drive shows **✅ Connected**

## Step 5: Try It Out!

### Test Calculator (no auth needed)
```
"What's 25 + 17?"
```

### Test Google Drive (after connecting)
```
"List my recent files"
"Search for 'report' in my Drive"
```

## That's It! 🎉

Your chat app now has:
- ✅ Calculator tools (local, no auth)
- ✅ Google Drive tools (OAuth authenticated)
- ✅ Persistent authentication (won't ask again)
- ✅ Automatic token refresh

## Next Steps

- See [SETUP.md](./SETUP.md) for detailed Google OAuth setup
- See [IMPLEMENTATION_SUMMARY.md](../../development_notes/IMPLEMENTATION_SUMMARY.md) for technical details
- Add more MCP servers by editing `MCP_SERVERS` in `chat_backend.py`

## Troubleshooting

**Can't get Google OAuth credentials?**
→ See [SETUP.md](./SETUP.md) Step 1

**Imports not resolving?**
→ Run `uv sync` to install Python dependencies

**Popup blocked?**
→ Allow popups for localhost:3000 in browser settings

**Token errors?**
→ Click "Disconnect" then "Connect with Google" again

---

**Need help?** Check the detailed guides:
- [SETUP.md](./SETUP.md) - Complete setup guide
- [IMPLEMENTATION_SUMMARY.md](../../development_notes/IMPLEMENTATION_SUMMARY.md) - Technical details

