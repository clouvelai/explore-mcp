"""
Shared Google authentication utilities for MCP servers.

This module provides common OAuth authentication functionality for Google APIs
used by Gmail and Google Drive MCP servers.
"""

import os
from typing import Any, Dict

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import Resource, build


class GoogleServiceManager:
    """Manages Google API service instances with shared authentication."""
    
    def __init__(self):
        self._services: Dict[str, Resource] = {}
        self._credentials = None
    
    def _get_credentials(self) -> Credentials:
        """Get or create Google OAuth credentials."""
        if self._credentials is None:
            access_token = os.getenv('GOOGLE_ACCESS_TOKEN')
            refresh_token = os.getenv('GOOGLE_REFRESH_TOKEN')
            
            if not access_token:
                raise ValueError("GOOGLE_ACCESS_TOKEN environment variable not set")
            
            # Create credentials
            self._credentials = Credentials(
                token=access_token,
                refresh_token=refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=os.getenv('GOOGLE_CLIENT_ID'),
                client_secret=os.getenv('GOOGLE_CLIENT_SECRET')
            )
            
            # Refresh token if needed
            if self._credentials.expired and self._credentials.refresh_token:
                self._credentials.refresh(Request())
        
        return self._credentials
    
    def get_service(self, service_name: str, version: str) -> Resource:
        """Get or create a Google API service instance.
        
        Args:
            service_name: Name of the Google service (e.g., 'gmail', 'drive', 'sheets')
            version: Version of the API (e.g., 'v1', 'v3', 'v4')
            
        Returns:
            Google API service resource
        """
        service_key = f"{service_name}_{version}"
        
        if service_key not in self._services:
            credentials = self._get_credentials()
            self._services[service_key] = build(service_name, version, credentials=credentials)
        
        return self._services[service_key]
    
    def get_gmail_service(self) -> Resource:
        """Get Gmail API service instance."""
        return self.get_service('gmail', 'v1')
    
    def get_drive_service(self) -> Resource:
        """Get Google Drive API service instance."""
        return self.get_service('drive', 'v3')
    
    def get_sheets_service(self) -> Resource:
        """Get Google Sheets API service instance."""
        return self.get_service('sheets', 'v4')


# Global service manager instance
_service_manager = GoogleServiceManager()


def get_gmail_service() -> Resource:
    """Get Gmail API service instance."""
    return _service_manager.get_gmail_service()


def get_drive_service() -> Resource:
    """Get Google Drive API service instance."""
    return _service_manager.get_drive_service()


def get_sheets_service() -> Resource:
    """Get Google Sheets API service instance."""
    return _service_manager.get_sheets_service()