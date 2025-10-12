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
from googleapiclient.http import MediaIoBaseUpload
import io

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

@mcp.tool()
def read_file(file_id: str) -> str:
    """Read the content of a file from Google Drive.
    
    Args:
        file_id: The ID of the file to read
        
    Returns:
        The file content as text, or an error message
    """
    try:
        service = get_drive_service()
        
        # First get file metadata to determine the type
        file_metadata = service.files().get(fileId=file_id, fields="id, name, mimeType").execute()
        
        file_name = file_metadata.get('name', 'Unknown')
        mime_type = file_metadata.get('mimeType', '')
        
        # Handle Google Workspace documents (need to export)
        if mime_type.startswith('application/vnd.google-apps.'):
            if 'document' in mime_type:
                # Google Docs -> Plain text
                export_request = service.files().export(fileId=file_id, mimeType='text/plain')
            elif 'spreadsheet' in mime_type:
                # Google Sheets -> CSV
                export_request = service.files().export(fileId=file_id, mimeType='text/csv')
            elif 'presentation' in mime_type:
                # Google Slides -> Plain text
                export_request = service.files().export(fileId=file_id, mimeType='text/plain')
            else:
                return f"Cannot read Google Workspace file type: {mime_type}"
            
            file_content = export_request.execute()
            content_str = file_content.decode('utf-8')
            
        else:
            # Handle regular files (uploaded files, not Google Workspace docs)
            try:
                # Download file content
                request = service.files().get_media(fileId=file_id)
                file_content = request.execute()
                
                # Try to decode as text
                try:
                    content_str = file_content.decode('utf-8')
                except UnicodeDecodeError:
                    # If it's not text, return info about the binary file
                    size = len(file_content)
                    return f"📄 Binary file: {file_name}\nSize: {size} bytes\nMIME Type: {mime_type}\n\nThis is a binary file and cannot be displayed as text."
                    
            except HttpError as e:
                if e.resp.status == 403:
                    return f"Cannot download file content for: {file_name}\nThis may be a Google Workspace document that needs to be exported in a specific format."
                else:
                    raise e
        
        # Return the content with file info
        output = f"📄 File: {file_name}\n"
        output += f"Type: {mime_type}\n"
        output += f"Content:\n{'='*50}\n"
        output += content_str
        
        return output
        
    except HttpError as error:
        if error.resp.status == 404:
            return f"File not found with ID: {file_id}"
        return f"An error occurred: {error}"
    except Exception as error:
        return f"An unexpected error occurred: {error}"

@mcp.tool()
def update_spreadsheet_cells(spreadsheet_id: str, range: str, values: List[List[str]]) -> str:
    """Update cells in a Google Sheets spreadsheet.
    
    This tool ONLY works with Google Sheets spreadsheets, not other file types.
    
    Args:
        spreadsheet_id: The ID of the Google Sheets spreadsheet
        range: A1 notation range (e.g., "Sheet1!A1:C3" or "A1:B2")
        values: 2D list of values to write (rows, then columns)
        
    Returns:
        Success message with number of cells updated
    
    Example:
        update_spreadsheet_cells(
            spreadsheet_id="1abc123", 
            range="Sheet1!A1:B2",
            values=[["Name", "Score"], ["Alice", "100"]]
        )
    """
    try:
        # Get credentials from Drive service
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
        
        # Build the Sheets service
        sheets_service = build('sheets', 'v4', credentials=creds)
        
        # First verify this is actually a Google Sheets file
        drive_service = get_drive_service()
        file_metadata = drive_service.files().get(fileId=spreadsheet_id, fields="name, mimeType").execute()
        
        if file_metadata.get('mimeType') != 'application/vnd.google-apps.spreadsheet':
            return f"❌ Error: This file is not a Google Sheets spreadsheet.\nFile: {file_metadata.get('name')}\nType: {file_metadata.get('mimeType')}"
        
        # Prepare the update body
        body = {
            'values': values
        }
        
        # Update the spreadsheet
        result = sheets_service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=range,
            valueInputOption='USER_ENTERED',  # Allows formulas and automatic parsing
            body=body
        ).execute()
        
        updated_cells = result.get('updatedCells', 0)
        updated_rows = result.get('updatedRows', 0)
        updated_columns = result.get('updatedColumns', 0)
        updated_range = result.get('updatedRange', range)
        
        return f"✅ Successfully updated spreadsheet: {file_metadata.get('name')}\n" \
               f"Range updated: {updated_range}\n" \
               f"Cells updated: {updated_cells}\n" \
               f"Rows affected: {updated_rows}\n" \
               f"Columns affected: {updated_columns}"
        
    except HttpError as error:
        if error.resp.status == 404:
            return f"❌ Spreadsheet not found with ID: {spreadsheet_id}"
        elif error.resp.status == 403:
            return f"❌ Permission denied. You may not have edit access to this spreadsheet."
        elif error.resp.status == 400:
            return f"❌ Invalid request. Check that the range '{range}' is valid and matches the size of your values."
        return f"❌ An error occurred: {error}"
    except Exception as error:
        return f"❌ An unexpected error occurred: {error}"

@mcp.tool()
def read_spreadsheet_cells(spreadsheet_id: str, range: str) -> str:
    """Read cells from a Google Sheets spreadsheet.
    
    This tool ONLY works with Google Sheets spreadsheets, not other file types.
    
    Args:
        spreadsheet_id: The ID of the Google Sheets spreadsheet
        range: A1 notation range (e.g., "Sheet1!A1:C10" or "A1:B2")
        
    Returns:
        The cell values in a formatted table
    """
    try:
        # Get credentials from Drive service
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
        
        # Build the Sheets service
        sheets_service = build('sheets', 'v4', credentials=creds)
        
        # First verify this is actually a Google Sheets file
        drive_service = get_drive_service()
        file_metadata = drive_service.files().get(fileId=spreadsheet_id, fields="name, mimeType").execute()
        
        if file_metadata.get('mimeType') != 'application/vnd.google-apps.spreadsheet':
            return f"❌ Error: This file is not a Google Sheets spreadsheet.\nFile: {file_metadata.get('name')}\nType: {file_metadata.get('mimeType')}"
        
        # Read the spreadsheet
        result = sheets_service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=range
        ).execute()
        
        values = result.get('values', [])
        
        if not values:
            return f"📊 Spreadsheet: {file_metadata.get('name')}\nRange: {range}\n\nNo data found in the specified range."
        
        # Format the output as a table
        output = f"📊 Spreadsheet: {file_metadata.get('name')}\n"
        output += f"Range: {range}\n"
        output += f"Data:\n{'='*50}\n"
        
        # Find the maximum width for each column for better formatting
        col_widths = []
        for col_idx in range(max(len(row) for row in values)):
            max_width = 0
            for row in values:
                if col_idx < len(row):
                    max_width = max(max_width, len(str(row[col_idx])))
            col_widths.append(min(max_width, 30))  # Cap at 30 chars
        
        # Display the data
        for row in values:
            formatted_row = []
            for col_idx, cell in enumerate(row):
                cell_str = str(cell)[:30]  # Truncate if too long
                if col_idx < len(col_widths):
                    formatted_row.append(cell_str.ljust(col_widths[col_idx]))
                else:
                    formatted_row.append(cell_str)
            output += " | ".join(formatted_row) + "\n"
        
        return output
        
    except HttpError as error:
        if error.resp.status == 404:
            return f"❌ Spreadsheet not found with ID: {spreadsheet_id}"
        elif error.resp.status == 403:
            return f"❌ Permission denied. You may not have access to this spreadsheet."
        elif error.resp.status == 400:
            return f"❌ Invalid request. Check that the range '{range}' is valid."
        return f"❌ An error occurred: {error}"
    except Exception as error:
        return f"❌ An unexpected error occurred: {error}"

@mcp.tool()
def create_text_file(name: str, content: str, parent_folder_id: str = None) -> str:
    """Create a new text file in Google Drive.
    
    Args:
        name: The name for the new file
        content: The content for the file
        parent_folder_id: Optional parent folder ID (defaults to root)
        
    Returns:
        Information about the created file
    """
    try:
        service = get_drive_service()
        
        # Prepare file metadata
        file_metadata = {'name': name}
        if parent_folder_id:
            file_metadata['parents'] = [parent_folder_id]
        
        # Convert string content to bytes
        content_bytes = content.encode('utf-8')
        
        # Create media upload object
        media = MediaIoBaseUpload(
            io.BytesIO(content_bytes),
            mimetype='text/plain',
            resumable=True
        )
        
        # Create the file
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, name, mimeType, createdTime'
        ).execute()
        
        return f"✅ Successfully created file: {file.get('name')}\nFile ID: {file.get('id')}\nType: {file.get('mimeType')}\nCreated: {file.get('createdTime')}\nContent size: {len(content_bytes)} bytes"
        
    except HttpError as error:
        return f"An error occurred: {error}"
    except Exception as error:
        return f"An unexpected error occurred: {error}"

if __name__ == "__main__":
    # FastMCP handles all the stdio server setup automatically
    mcp.run()
