# Gmail MCP Integration Setup Guide

This guide walks you through setting up Gmail OAuth authentication for your MCP chat application.

## Prerequisites

- Python 3.10+
- Node.js 16+
- A Google account
- OpenAI API key

## Important: Gmail vs Google Drive OAuth

Gmail and Google Drive can use the **same Google Cloud Project** and **same OAuth credentials**, but they require different API scopes. You can either:

1. **Option A (Recommended)**: Use the same OAuth client for both Gmail and Google Drive
2. **Option B**: Create separate OAuth clients for each service

This guide assumes **Option A** - using the same credentials with expanded scopes.

## Step 1: Configure Google Cloud Console

### 1.1 Go to Google Cloud Console

Visit: https://console.cloud.google.com/

### 1.2 Select Your Existing Project (or Create New)

1. Click on the project dropdown at the top
2. If you already have a project from Google Drive setup, **select it**
3. OR click "NEW PROJECT" to create a new one (e.g., "MCP Chat App")

### 1.3 Enable Gmail API

1. In the left sidebar, go to **APIs & Services** > **Library**
2. Search for "Gmail API"
3. Click on it and press **ENABLE**

### 1.4 Update OAuth Scopes (If Using Existing OAuth Client)

If you already have OAuth credentials from Google Drive setup:

1. Go to **APIs & Services** > **OAuth consent screen**
2. Click **EDIT APP**
3. Click **SAVE AND CONTINUE** until you reach the **Scopes** section
4. Click **ADD OR REMOVE SCOPES**
5. Search for and add these Gmail scopes:
   - `https://www.googleapis.com/auth/gmail.readonly` - Read emails
   - `https://www.googleapis.com/auth/gmail.modify` - Mark as read/unread
   - `https://www.googleapis.com/auth/gmail.send` - Send emails
   - `https://www.googleapis.com/auth/gmail.labels` - Manage labels
6. Click **UPDATE** then **SAVE AND CONTINUE**

### 1.5 Create OAuth 2.0 Credentials (If New Project)

Only do this if you're creating a new project:

1. Go to **APIs & Services** > **Credentials**
2. Click **+ CREATE CREDENTIALS** > **OAuth client ID**
3. If prompted, configure the OAuth consent screen:
   - User Type: **External** (for testing) or **Internal** (for organization)
   - App name: "MCP Chat App"
   - User support email: Your email
   - Developer contact: Your email
   - Click **SAVE AND CONTINUE**
   - Scopes: Add the Gmail scopes listed above
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

### 1.6 Verify Redirect URI (If Using Existing Credentials)

1. Go to **APIs & Services** > **Credentials**
2. Find your existing OAuth 2.0 Client ID
3. Click the edit icon (pencil)
4. Make sure `http://localhost:5001/api/oauth/callback` is in **Authorized redirect URIs**
5. Click **SAVE**

## Step 2: Configure Your Application

### 2.1 Use Existing .env File

If you already have Google Drive configured, you can use the **same credentials**:

```bash
# .env (no changes needed if you already have these)
OPENAI_API_KEY=sk-your-actual-openai-key
FLASK_SECRET_KEY=super-secret-random-string-here
GOOGLE_CLIENT_ID=123456789-abcdefg.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-your-secret-here
```

The same `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` will work for both Gmail and Google Drive!

### 2.2 For New Setup

If starting fresh, copy and edit the environment file:

```bash
cp ENV_TEMPLATE .env
```

Then edit `.env` with your credentials as shown above.

## Step 3: Install Dependencies

Dependencies are already included in `pyproject.toml`. Just run:

```bash
# Install Python dependencies
uv sync

# OR if using pip:
pip install -r pyproject.toml
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
  - Gmail: 🔐 Requires auth
```

### 4.2 Start Frontend (in a new terminal)

```bash
cd chat-frontend
npm start
```

Browser should open at: http://localhost:3000

## Step 5: Connect Gmail

### 5.1 In the Web UI

1. You'll see server cards including:
   - **Gmail** (⚠️ Not Connected)

2. Click **"Connect with Google"** on the Gmail card

3. A popup window will open with Google's authentication page

4. **Sign in** with your Google account (if not already signed in)

5. **Grant permissions** when prompted:
   - Read, compose, send, and permanently delete all your email from Gmail
   - See, edit, create, and delete all your Google Drive files
   - (If you already granted Google Drive permissions, you might see additional Gmail permissions)

6. The popup will close automatically after successful authentication

7. Gmail should now show **✅ Connected**

**Note**: If you previously authenticated with Google Drive, you'll need to **reconnect** to grant the additional Gmail scopes. Just:
- Click "Disconnect" on the Google Drive card
- Click "Connect with Google" on either card
- Grant all permissions in the new OAuth flow
- Both Gmail and Google Drive will now be connected!

## Step 6: Test Gmail Operations!

Try these commands in the chat:

### List and Search
- "Show me my recent emails"
- "List my last 5 emails"
- "Search for emails from john@example.com"
- "Find unread messages"
- "Search for emails with subject 'meeting'"

### Read Messages
- "Read the first email"
- "Show me the full content of message ID abc123"

### Check Inbox
- "How many unread emails do I have?"
- "Show me unread messages"

### Manage Messages
- "Mark message abc123 as read"
- "Mark message abc123 as unread"

### Send Email (use with caution!)
- "Send an email to test@example.com with subject 'Hello' and body 'This is a test'"

### Labels
- "List all my Gmail labels"

## Security Note

**Be careful with the send_message tool!** The chat agent can send emails on your behalf. Always review what the agent plans to do before confirming actions.

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

### Error: "Insufficient Permission"

**Problem**: Gmail API not enabled or wrong scopes.

**Solution**:
1. Go to Google Cloud Console > APIs & Services > Library
2. Search for "Gmail API" and make sure it's enabled
3. Check OAuth consent screen has the required Gmail scopes
4. Disconnect and reconnect to get new scopes

### Need to Re-authenticate After Adding Gmail

**Problem**: Already connected Google Drive, now need Gmail access.

**Solution**:
1. Click "Disconnect" on Google Drive
2. Click "Connect with Google" again
3. Grant all permissions (Drive + Gmail)
4. Both services will now work

### Can't Read Email Content

**Problem**: Emails show metadata but not content.

**Solution**:
1. Make sure `gmail.readonly` scope is granted
2. Try disconnecting and reconnecting
3. Some emails (HTML-only) might not display well as plain text

## Gmail API Query Examples

When searching messages, you can use powerful Gmail search operators:

- `is:unread` - Unread messages
- `is:read` - Read messages
- `from:email@example.com` - From specific sender
- `to:email@example.com` - To specific recipient
- `subject:meeting` - Subject contains "meeting"
- `has:attachment` - Has attachments
- `after:2024/01/01` - After a specific date
- `before:2024/12/31` - Before a specific date
- `label:work` - Messages with specific label

Combine them: `from:boss@work.com is:unread subject:urgent`

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
- These tokens can read/send emails!

## Disconnecting

To revoke access:

### From the UI
1. Click **"Disconnect"** on the Gmail server card
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
│  Gmail MCP       │  │  Google OAuth & │
│  Server          │  │  Gmail API      │
│  (local)         │  │  (remote)       │
└──────────────────┘  └─────────────────┘
```

## What's Different from Google Drive?

The Gmail MCP server is structured similarly to Google Drive but with email-specific operations:

**Google Drive Tools**:
- list_files, search_files, read_file, edit_file, create_text_file

**Gmail Tools**:
- list_messages, search_messages, read_message, send_message
- mark_as_read, mark_as_unread, get_unread_count, list_labels

**Shared Infrastructure**:
- Same OAuth handler
- Same token storage
- Same authentication flow
- Can use same Google Cloud project

## Next Steps

- Add more Gmail operations (delete, archive, trash)
- Implement attachment handling
- Add Gmail filters and rules management
- Create email templates
- Combine with Google Drive for attachment operations

## Getting Help

If you run into issues:

1. Check the backend console logs
2. Check browser console (F12)
3. Verify your .env file is correct
4. Make sure Gmail API is enabled in Google Cloud Console
5. Verify OAuth scopes include Gmail permissions
6. Try disconnecting and reconnecting

Happy emailing! 📧


