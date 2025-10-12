"""
OAuth 2.0 authentication handler using google-auth library.
Handles Google Drive authentication with persistent token storage.
"""

from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import json
from typing import Optional

class GoogleOAuthHandler:
    """Handle OAuth 2.0 authentication for Google services"""
    
    # Google Drive scopes
    SCOPES = [
        'https://www.googleapis.com/auth/drive.readonly',
        'https://www.googleapis.com/auth/drive.file',
        'https://www.googleapis.com/auth/drive.metadata.readonly'
    ]
    
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str = "http://localhost:5001/api/oauth/callback"):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.flow = None
    
    def get_client_config(self) -> dict:
        """Generate client config for google-auth"""
        return {
            "web": {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "redirect_uris": [self.redirect_uri],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token"
            }
        }
    
    def get_authorization_url(self) -> tuple[str, str]:
        """
        Get the authorization URL for user to authenticate.
        Returns: (authorization_url, state)
        """
        self.flow = Flow.from_client_config(
            self.get_client_config(),
            scopes=self.SCOPES,
            redirect_uri=self.redirect_uri
        )
        
        authorization_url, state = self.flow.authorization_url(
            access_type='offline',  # Get refresh token
            prompt='consent',  # Force consent to ensure refresh token
            include_granted_scopes='true'
        )
        
        return authorization_url, state
    
    def exchange_code_for_tokens(self, code: str, state: str = None) -> dict:
        """
        Exchange authorization code for access tokens.
        Returns: dict with access_token, refresh_token, etc.
        """
        if not self.flow:
            # Recreate flow if not exists
            self.flow = Flow.from_client_config(
                self.get_client_config(),
                scopes=self.SCOPES,
                redirect_uri=self.redirect_uri,
                state=state
            )
        
        # Fetch token
        self.flow.fetch_token(code=code)
        
        # Get credentials
        creds = self.flow.credentials
        
        # Convert to dict
        return {
            'access_token': creds.token,
            'refresh_token': creds.refresh_token,
            'token_type': 'Bearer',
            'expires_in': 3600,  # Default to 1 hour
            'scope': ' '.join(self.SCOPES)
        }
    
    def refresh_access_token(self, refresh_token: str) -> dict:
        """
        Refresh an expired access token using refresh token.
        Returns: dict with new access_token
        """
        creds = Credentials(
            token=None,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=self.client_id,
            client_secret=self.client_secret,
            scopes=self.SCOPES
        )
        
        # Refresh the token
        creds.refresh(Request())
        
        return {
            'access_token': creds.token,
            'refresh_token': refresh_token,  # Keep original
            'token_type': 'Bearer',
            'expires_in': 3600,
            'scope': ' '.join(self.SCOPES)
        }
    
    @staticmethod
    def credentials_to_dict(creds: Credentials) -> dict:
        """Convert Credentials object to dict for storage"""
        return {
            'access_token': creds.token,
            'refresh_token': creds.refresh_token,
            'token_type': 'Bearer',
            'expires_in': 3600,
            'scope': ' '.join(creds.scopes) if creds.scopes else ''
        }
    
    @staticmethod
    def dict_to_credentials(token_dict: dict, client_id: str, client_secret: str) -> Credentials:
        """Convert dict to Credentials object"""
        return Credentials(
            token=token_dict['access_token'],
            refresh_token=token_dict.get('refresh_token'),
            token_uri="https://oauth2.googleapis.com/token",
            client_id=client_id,
            client_secret=client_secret
        )

