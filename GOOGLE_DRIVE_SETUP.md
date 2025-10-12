# Google Drive MCP Integration Setup Guide

This guide walks you through setting up Google Drive OAuth authentication for your MCP chat application.

## Prerequisites

- Python 3.10+
- Node.js 16+
- A Google account
- OpenAI API key

## Step 1: Get Google OAuth Credentials

### 1.1 Go to Google Cloud Console

Visit: https://console.cloud.google.com/

### 1.2 Create or Select a Project

1. Click on the project dropdown at the top
2. Click "NEW PROJECT" or select an existing project
3. Give it a name (e.g., "MCP Chat App")

### 1.3 Enable Google Drive API

1. In the left sidebar, go to **APIs & Services** > **Library**
2. Search for "Google Drive API"
3. Click on it and press **ENABLE**

### 1.4 Create OAuth 2.0 Credentials

1. Go to **APIs & Services** > **Credentials**
2. Click **+ CREATE CREDENTIALS** > **OAuth client ID**
3. If prompted, configure the OAuth consent screen:
   - User Type: **External** (for testing) or **Internal** (for organization)
   - App name: "MCP Chat App"
   - User support email: Your email
   - Developer contact: Your email
   - Click **SAVE AND CONTINUE**
   - Scopes: Skip for now (click **SAVE AND CONTINUE**)
   - Test users: Add your email if using External
   - Click **SAVE AND CONTINUE**

4. Back at Create OAuth client ID:
   - Application type: **Web application**
   - Name: "MCP Chat OAuth Client"
   - Authorized redirect URIs: Click **+ ADD URI**
     - Add: `http://localhost:5001/api/oauth/callback`
   - Click **CREATE**

5. **IMPORTANT**: Copy your **Client ID** and **Client Secret**
   - Save them somewhere secure!

## Step 2: Configure Your Application

### 2.1 Copy Environment Template

```bash
cp ENV_TEMPLATE .env
```

### 2.2 Edit .env File

```bash
# .env
OPENAI_API_KEY=sk-your-actual-openai-key

# Generate a random secret key (or use any random string)
FLASK_SECRET_KEY=super-secret-random-string-here

# Paste your Google OAuth credentials here
GOOGLE_CLIENT_ID=123456789-abcdefg.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-your-secret-here
```

## Step 3: Install Dependencies

### 3.1 Backend (Python)

```bash
# Install Python dependencies
uv sync

# OR if using pip:
pip install -r pyproject.toml
```

### 3.2 Frontend (React)

```bash
cd chat-frontend
npm install
cd ..
```

## Step 4: Run the Application

### 4.1 Start Backend

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

### 4.2 Start Frontend (in a new terminal)

```bash
cd chat-frontend
npm start
```

Browser should open at: http://localhost:3000

## Step 5: Connect Google Drive

### 5.1 In the Web UI

1. You'll see two server cards:
   - **Calculator** (✅ Connected)
   - **Google Drive** (⚠️ Not Connected)

2. Click **"Connect with Google"** on the Google Drive card

3. A popup window will open with Google's authentication page

4. **Sign in** with your Google account

5. **Grant permissions** when prompted:
   - View and manage Google Drive files
   - See basic info about your files

6. The popup will close automatically after successful authentication

7. Google Drive should now show **✅ Connected**

## Step 6: Test It Out!

Try these commands in the chat:

### Calculator (No auth needed)
- "What's 25 + 17?"
- "Add 100 and 250"

### Google Drive (After connecting)
- "List my recent Google Drive files"
- "Search for 'report' in my Drive"
- "Show me files modified today"
- "Find all PDFs in my Drive"

## Troubleshooting

### Error: "redirect_uri_mismatch"

**Problem**: The redirect URI doesn't match what's configured in Google Cloud Console.

**Solution**:
1. Go to Google Cloud Console > Credentials
2. Edit your OAuth client
3. Make sure `http://localhost:5001/api/oauth/callback` is in Authorized redirect URIs
4. Save and try again

### Error: "Access blocked: This app hasn't been verified"

**Problem**: Your app isn't verified by Google (normal for development).

**Solution**:
1. On the error page, click **"Advanced"**
2. Click **"Go to [Your App Name] (unsafe)"**
3. This only happens in development - safe to proceed

### Popup Blocked

**Problem**: Browser blocked the OAuth popup.

**Solution**:
1. Allow popups for localhost:3000
2. Click "Connect with Google" again

### Token Expired

**Problem**: Your OAuth token expired (usually after 1 hour).

**Solution**:
- Tokens refresh automatically!
- If you see errors, just click "Disconnect" then "Connect with Google" again

### Can't Find Files

**Problem**: The Google Drive MCP server can't access your files.

**Solution**:
1. Make sure you granted all permissions during OAuth
2. Try disconnecting and reconnecting with Google
3. Check the backend console for error messages

## Token Storage

OAuth tokens are stored securely in:
```
explore-mcp/.mcp_data/tokens.db
```

This SQLite database contains:
- Access tokens (valid for ~1 hour)
- Refresh tokens (used to get new access tokens)
- Expiration timestamps

**Security Note**: This file contains sensitive tokens! 
- Don't commit it to git (it's in .gitignore)
- Don't share it

## Disconnecting

To revoke access:

### From the UI
1. Click **"Disconnect"** on the Google Drive server card
2. Tokens are deleted from local storage

### From Google
1. Visit: https://myaccount.google.com/permissions
2. Find your app
3. Click **"Remove Access"**

## Architecture

```
┌─────────────────────────────────────┐
│  Browser (React App)                │
│  - Server cards with connect button │
│  - OAuth popup window                │
└─────────────────────────────────────┘
              ↕ HTTP
┌─────────────────────────────────────┐
│  Flask Backend (chat_backend.py)    │
│  - Token storage (SQLite)           │
│  - OAuth flow management            │
│  - MCP server orchestration         │
└─────────────────────────────────────┘
       ↕ stdio              ↕ HTTPS
┌──────────────────┐  ┌─────────────────┐
│  Google Drive    │  │  Google OAuth & │
│  MCP Server      │  │  Drive API      │
│  (local)         │  │  (remote)       │
└──────────────────┘  └─────────────────┘
```

## Next Steps

- Add more MCP servers (Slack, GitHub, etc.)
- Implement file upload/download
- Add user authentication for the chat app itself
- Deploy to production (requires HTTPS)

## Getting Help

If you run into issues:

1. Check the backend console logs
2. Check browser console (F12)
3. Verify your .env file is correct
4. Make sure all dependencies are installed
5. Try disconnecting and reconnecting

Happy coding! 🚀

