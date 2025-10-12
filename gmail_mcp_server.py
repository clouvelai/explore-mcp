#!/usr/bin/env python3
"""
Gmail MCP Server

This server provides tools to interact with Gmail using the Gmail API.
It requires OAuth authentication via environment variables.
"""

import asyncio
import json
import os
import base64
from typing import Any, Dict, List
from fastmcp import FastMCP
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Create the FastMCP server instance
mcp = FastMCP("gmail")

# Initialize Gmail service
gmail_service = None

def get_gmail_service():
    """Get or create Gmail service instance."""
    global gmail_service
    
    if gmail_service is None:
        access_token = os.getenv('GOOGLE_ACCESS_TOKEN')
        refresh_token = os.getenv('GOOGLE_REFRESH_TOKEN')
        
        if not access_token:
            raise ValueError("GOOGLE_ACCESS_TOKEN environment variable not set")
        
        # Create credentials
        creds = Credentials(
            token=access_token,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=os.getenv('GOOGLE_CLIENT_ID'),
            client_secret=os.getenv('GOOGLE_CLIENT_SECRET')
        )
        
        # Refresh token if needed
        if creds.expired:
            creds.refresh(Request())
        
        # Build the service
        gmail_service = build('gmail', 'v1', credentials=creds)
    
    return gmail_service

@mcp.tool()
def list_messages(max_results: int = 10, query: str = "") -> str:
    """List messages in Gmail inbox.
    
    Args:
        max_results: Maximum number of messages to return (default: 10)
        query: Optional search query (e.g., "is:unread", "from:example@gmail.com")
        
    Returns:
        A formatted string listing the messages
    """
    try:
        service = get_gmail_service()
        
        # List messages
        results = service.users().messages().list(
            userId='me',
            maxResults=max_results,
            q=query if query else None
        ).execute()
        
        messages = results.get('messages', [])
        
        if not messages:
            return "No messages found in Gmail."
        
        output = f"Found {len(messages)} messages:\n\n"
        
        # Get details for each message
        for msg in messages:
            msg_data = service.users().messages().get(
                userId='me',
                id=msg['id'],
                format='metadata',
                metadataHeaders=['From', 'Subject', 'Date']
            ).execute()
            
            headers = msg_data['payload']['headers']
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
            date = next((h['value'] for h in headers if h['name'] == 'Date'), 'Unknown')
            
            # Check if message is unread
            labels = msg_data.get('labelIds', [])
            is_unread = 'UNREAD' in labels
            unread_marker = '🔵 ' if is_unread else ''
            
            output += f"{unread_marker}📧 {subject}\n"
            output += f"   From: {sender}\n"
            output += f"   Date: {date}\n"
            output += f"   ID: {msg['id']}\n\n"
        
        return output
        
    except HttpError as error:
        return f"An error occurred: {error}"
    except Exception as error:
        return f"An unexpected error occurred: {error}"

@mcp.tool()
def search_messages(query: str, max_results: int = 10) -> str:
    """Search for messages in Gmail.
    
    Args:
        query: Search query (e.g., "from:example@gmail.com", "subject:meeting", "is:unread")
        max_results: Maximum number of results to return (default: 10)
        
    Returns:
        A formatted string with search results
    """
    try:
        service = get_gmail_service()
        
        # Search messages
        results = service.users().messages().list(
            userId='me',
            maxResults=max_results,
            q=query
        ).execute()
        
        messages = results.get('messages', [])
        
        if not messages:
            return f"No messages found matching query: '{query}'"
        
        output = f"Found {len(messages)} messages matching '{query}':\n\n"
        
        # Get details for each message
        for msg in messages:
            msg_data = service.users().messages().get(
                userId='me',
                id=msg['id'],
                format='metadata',
                metadataHeaders=['From', 'Subject', 'Date']
            ).execute()
            
            headers = msg_data['payload']['headers']
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
            date = next((h['value'] for h in headers if h['name'] == 'Date'), 'Unknown')
            
            # Check if message is unread
            labels = msg_data.get('labelIds', [])
            is_unread = 'UNREAD' in labels
            unread_marker = '🔵 ' if is_unread else ''
            
            output += f"{unread_marker}📧 {subject}\n"
            output += f"   From: {sender}\n"
            output += f"   Date: {date}\n"
            output += f"   ID: {msg['id']}\n\n"
        
        return output
        
    except HttpError as error:
        return f"An error occurred: {error}"
    except Exception as error:
        return f"An unexpected error occurred: {error}"

@mcp.tool()
def read_message(message_id: str) -> str:
    """Read the full content of a specific message.
    
    Args:
        message_id: The ID of the message to read
        
    Returns:
        The full message content
    """
    try:
        service = get_gmail_service()
        
        # Get message
        msg_data = service.users().messages().get(
            userId='me',
            id=message_id,
            format='full'
        ).execute()
        
        headers = msg_data['payload']['headers']
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
        sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
        date = next((h['value'] for h in headers if h['name'] == 'Date'), 'Unknown')
        to = next((h['value'] for h in headers if h['name'] == 'To'), 'Unknown')
        
        # Extract body
        body = ""
        if 'parts' in msg_data['payload']:
            for part in msg_data['payload']['parts']:
                if part['mimeType'] == 'text/plain':
                    if 'data' in part['body']:
                        body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                        break
                elif part['mimeType'] == 'text/html':
                    if 'data' in part['body']:
                        body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
        else:
            if 'data' in msg_data['payload']['body']:
                body = base64.urlsafe_b64decode(msg_data['payload']['body']['data']).decode('utf-8')
        
        # Format output
        output = f"📧 Email Message\n"
        output += f"{'='*60}\n"
        output += f"Subject: {subject}\n"
        output += f"From: {sender}\n"
        output += f"To: {to}\n"
        output += f"Date: {date}\n"
        output += f"Message ID: {message_id}\n"
        output += f"{'='*60}\n\n"
        output += body if body else "[No text content available]"
        
        return output
        
    except HttpError as error:
        if error.resp.status == 404:
            return f"Message not found with ID: {message_id}"
        return f"An error occurred: {error}"
    except Exception as error:
        return f"An unexpected error occurred: {error}"

@mcp.tool()
def get_unread_count() -> str:
    """Get the count of unread messages in the inbox.
    
    Returns:
        The number of unread messages
    """
    try:
        service = get_gmail_service()
        
        # Get unread messages
        results = service.users().messages().list(
            userId='me',
            q='is:unread',
            maxResults=1
        ).execute()
        
        # Get the total count from resultSizeEstimate
        unread_count = results.get('resultSizeEstimate', 0)
        
        return f"📬 You have {unread_count} unread message{'s' if unread_count != 1 else ''} in your inbox."
        
    except HttpError as error:
        return f"An error occurred: {error}"
    except Exception as error:
        return f"An unexpected error occurred: {error}"

@mcp.tool()
def create_draft(to: str, subject: str, body: str) -> str:
    """Create an email draft (does not send).
    
    Args:
        to: Recipient email address
        subject: Email subject
        body: Email body text
        
    Returns:
        Success message with draft ID
    """
    try:
        service = get_gmail_service()
        
        # Create message
        message = MIMEText(body)
        message['to'] = to
        message['subject'] = subject
        
        # Encode message
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        
        # Create draft
        draft = service.users().drafts().create(
            userId='me',
            body={'message': {'raw': raw_message}}
        ).execute()
        
        return f"✅ Draft created successfully!\nDraft ID: {draft['id']}\nTo: {to}\nSubject: {subject}\n\nYou can review and send this draft from Gmail."
        
    except HttpError as error:
        return f"An error occurred: {error}"
    except Exception as error:
        return f"An unexpected error occurred: {error}"

@mcp.tool()
def mark_as_read(message_id: str) -> str:
    """Mark a message as read.
    
    Args:
        message_id: The ID of the message to mark as read
        
    Returns:
        Success message
    """
    try:
        service = get_gmail_service()
        
        # Remove UNREAD label
        service.users().messages().modify(
            userId='me',
            id=message_id,
            body={'removeLabelIds': ['UNREAD']}
        ).execute()
        
        return f"✅ Message marked as read: {message_id}"
        
    except HttpError as error:
        if error.resp.status == 404:
            return f"Message not found with ID: {message_id}"
        return f"An error occurred: {error}"
    except Exception as error:
        return f"An unexpected error occurred: {error}"

@mcp.tool()
def mark_as_unread(message_id: str) -> str:
    """Mark a message as unread.
    
    Args:
        message_id: The ID of the message to mark as unread
        
    Returns:
        Success message
    """
    try:
        service = get_gmail_service()
        
        # Add UNREAD label
        service.users().messages().modify(
            userId='me',
            id=message_id,
            body={'addLabelIds': ['UNREAD']}
        ).execute()
        
        return f"✅ Message marked as unread: {message_id}"
        
    except HttpError as error:
        if error.resp.status == 404:
            return f"Message not found with ID: {message_id}"
        return f"An error occurred: {error}"
    except Exception as error:
        return f"An unexpected error occurred: {error}"

@mcp.tool()
def list_labels() -> str:
    """List all labels in Gmail.
    
    Returns:
        A formatted string listing all labels
    """
    try:
        service = get_gmail_service()
        
        # Get labels
        results = service.users().labels().list(userId='me').execute()
        labels = results.get('labels', [])
        
        if not labels:
            return "No labels found."
        
        output = f"Found {len(labels)} labels:\n\n"
        
        for label in labels:
            label_type = label.get('type', 'user')
            output += f"🏷️  {label['name']}\n"
            output += f"   ID: {label['id']}\n"
            output += f"   Type: {label_type}\n\n"
        
        return output
        
    except HttpError as error:
        return f"An error occurred: {error}"
    except Exception as error:
        return f"An unexpected error occurred: {error}"

if __name__ == "__main__":
    # FastMCP handles all the stdio server setup automatically
    mcp.run()

