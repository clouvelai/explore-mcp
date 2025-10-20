"""
Authentication module for OAuth and token management.

This module handles all authentication-related functionality including:
- Google OAuth 2.0 flow for Gmail and Google Drive access
- Secure token storage and retrieval
- Token refresh and expiration management

Classes:
- GoogleOAuthHandler: Manages OAuth 2.0 authentication flow
- TokenStore: Persistent SQLite-based token storage

Usage:
    from backend.auth import GoogleOAuthHandler, TokenStore
    
    oauth_handler = GoogleOAuthHandler(client_id, client_secret)
    token_store = TokenStore()
"""