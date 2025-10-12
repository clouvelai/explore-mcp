#!/usr/bin/env python3
"""
Simple Google Drive MCP Server

This server provides tools to interact with Google Drive using the Google Drive API.
It requires OAuth authentication via environment variables.
"""

import asyncio
import json
import os
from typing import Any, Dict, List
from fastmcp import FastMCP
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Create the FastMCP server instance
mcp = FastMCP("google-drive")

# Initialize Google Drive service
drive_service = None

def get_drive_service():
    """Get or create Google Drive service instance."""
    global drive_service
    
    if drive_service is None:
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
        drive_service = build('drive', 'v3', credentials=creds)
    
    return drive_service

@mcp.tool()
def list_files(max_results: int = 10) -> str:
    """List files in Google Drive.
    
    Args:
        max_results: Maximum number of files to return (default: 10)
        
    Returns:
        A formatted string listing the files
    """
    try:
        service = get_drive_service()
        
        # Call the Drive v3 API
        results = service.files().list(
            pageSize=max_results,
            fields="nextPageToken, files(id, name, mimeType, createdTime, modifiedTime)"
        ).execute()
        
        items = results.get('files', [])
        
        if not items:
            return "No files found in Google Drive."
        
        output = f"Found {len(items)} files in Google Drive:\n\n"
        
        for item in items:
            output += f"📄 {item['name']}\n"
            output += f"   ID: {item['id']}\n"
            output += f"   Type: {item.get('mimeType', 'Unknown')}\n"
            output += f"   Modified: {item.get('modifiedTime', 'Unknown')}\n\n"
        
        return output
        
    except HttpError as error:
        return f"An error occurred: {error}"
    except Exception as error:
        return f"An unexpected error occurred: {error}"

@mcp.tool()
def search_files(query: str, max_results: int = 10) -> str:
    """Search for files in Google Drive.
    
    Args:
        query: Search query - can be natural language or Drive API format
        max_results: Maximum number of results to return (default: 10)
        
    Returns:
        A formatted string with search results
    """
    try:
        service = get_drive_service()
        
        # Convert natural language query to proper Drive API format
        # If the query doesn't contain Drive API operators, treat it as a name search
        if not any(op in query.lower() for op in ['contains', 'name=', 'mimeType=', 'modifiedTime>', 'createdTime>']):
            # Replace spaces and special chars, then format as name search
            clean_query = query.replace('+', ' ').replace('%20', ' ')
            # Use fullText search which searches file content and names
            formatted_query = f"fullText contains '{clean_query}'"
        else:
            # Use the query as-is if it already contains Drive API operators
            formatted_query = query
        
        # Call the Drive v3 API
        results = service.files().list(
            q=formatted_query,
            pageSize=max_results,
            fields="nextPageToken, files(id, name, mimeType, createdTime, modifiedTime)"
        ).execute()
        
        items = results.get('files', [])
        
        if not items:
            return f"No files found matching query: '{query}' (searched as: {formatted_query})"
        
        output = f"Found {len(items)} files matching '{query}':\n\n"
        
        for item in items:
            output += f"📄 {item['name']}\n"
            output += f"   ID: {item['id']}\n"
            output += f"   Type: {item.get('mimeType', 'Unknown')}\n"
            output += f"   Modified: {item.get('modifiedTime', 'Unknown')}\n\n"
        
        return output
        
    except HttpError as error:
        return f"An error occurred: {error}"
    except Exception as error:
        return f"An unexpected error occurred: {error}"

@mcp.tool()
def get_file_info(file_id: str) -> str:
    """Get detailed information about a specific file.
    
    Args:
        file_id: The ID of the file to get information about
        
    Returns:
        Detailed file information
    """
    try:
        service = get_drive_service()
        
        # Get file metadata
        file = service.files().get(
            fileId=file_id,
            fields="id, name, mimeType, size, createdTime, modifiedTime, owners, permissions"
        ).execute()
        
        output = f"📄 File Information\n"
        output += f"{'='*50}\n"
        output += f"Name: {file.get('name', 'Unknown')}\n"
        output += f"ID: {file.get('id', 'Unknown')}\n"
        output += f"Type: {file.get('mimeType', 'Unknown')}\n"
        output += f"Size: {file.get('size', 'Unknown')} bytes\n"
        output += f"Created: {file.get('createdTime', 'Unknown')}\n"
        output += f"Modified: {file.get('modifiedTime', 'Unknown')}\n"
        
        # Owner information
        owners = file.get('owners', [])
        if owners:
            output += f"Owner: {owners[0].get('displayName', 'Unknown')}\n"
        
        return output
        
    except HttpError as error:
        return f"An error occurred: {error}"
    except Exception as error:
        return f"An unexpected error occurred: {error}"

@mcp.tool()
def list_folders(max_results: int = 10) -> str:
    """List folders in Google Drive.
    
    Args:
        max_results: Maximum number of folders to return (default: 10)
        
    Returns:
        A formatted string listing the folders
    """
    try:
        service = get_drive_service()
        
        # Search for folders (mimeType = 'application/vnd.google-apps.folder')
        results = service.files().list(
            q="mimeType='application/vnd.google-apps.folder'",
            pageSize=max_results,
            fields="nextPageToken, files(id, name, mimeType, createdTime, modifiedTime)"
        ).execute()
        
        items = results.get('files', [])
        
        if not items:
            return "No folders found in Google Drive."
        
        output = f"Found {len(items)} folders in Google Drive:\n\n"
        
        for item in items:
            output += f"📁 {item['name']}\n"
            output += f"   ID: {item['id']}\n"
            output += f"   Modified: {item.get('modifiedTime', 'Unknown')}\n\n"
        
        return output
        
    except HttpError as error:
        return f"An error occurred: {error}"
    except Exception as error:
        return f"An unexpected error occurred: {error}"

@mcp.tool()
def recent_files(days: int = 7, max_results: int = 10) -> str:
    """Get recently modified files.
    
    Args:
        days: Number of days to look back (default: 7)
        max_results: Maximum number of files to return (default: 10)
        
    Returns:
        A formatted string with recent files
    """
    try:
        service = get_drive_service()
        
        from datetime import datetime, timedelta
        cutoff_date = datetime.now() - timedelta(days=days)
        cutoff_str = cutoff_date.isoformat() + 'Z'
        
        # Search for files modified after cutoff date
        results = service.files().list(
            q=f"modifiedTime > '{cutoff_str}'",
            pageSize=max_results,
            orderBy='modifiedTime desc',
            fields="nextPageToken, files(id, name, mimeType, createdTime, modifiedTime)"
        ).execute()
        
        items = results.get('files', [])
        
        if not items:
            return f"No files modified in the last {days} days."
        
        output = f"Files modified in the last {days} days:\n\n"
        
        for item in items:
            output += f"📄 {item['name']}\n"
            output += f"   ID: {item['id']}\n"
            output += f"   Type: {item.get('mimeType', 'Unknown')}\n"
            output += f"   Modified: {item.get('modifiedTime', 'Unknown')}\n\n"
        
        return output
        
    except HttpError as error:
        return f"An error occurred: {error}"
    except Exception as error:
        return f"An unexpected error occurred: {error}"

if __name__ == "__main__":
    # FastMCP handles all the stdio server setup automatically
    mcp.run()
