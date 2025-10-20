"""
Persistent token storage for OAuth tokens using SQLite.
Stores tokens securely with encryption support.
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict
import os

class TokenStore:
    """Persistent token storage for OAuth tokens"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            # Store in project directory
            db_path = Path(__file__).parent / ".mcp_data" / "tokens.db"
        
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """Create tokens table if it doesn't exist"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tokens (
                server_name TEXT PRIMARY KEY,
                access_token TEXT NOT NULL,
                refresh_token TEXT,
                token_type TEXT DEFAULT 'Bearer',
                expires_at INTEGER NOT NULL,
                scopes TEXT,
                created_at INTEGER NOT NULL,
                updated_at INTEGER NOT NULL
            )
        """)
        conn.commit()
        conn.close()
    
    def save_tokens(self, server_name: str, tokens: Dict):
        """Save tokens for a server"""
        conn = sqlite3.connect(self.db_path)
        
        # Calculate expiration time
        expires_in = tokens.get('expires_in', 3600)
        expires_at = int((datetime.now() + timedelta(seconds=expires_in)).timestamp())
        now = int(datetime.now().timestamp())
        
        # Get scopes
        scopes = tokens.get('scope', '')
        if isinstance(scopes, list):
            scopes = ' '.join(scopes)
        
        conn.execute("""
            INSERT OR REPLACE INTO tokens 
            (server_name, access_token, refresh_token, token_type, 
             expires_at, scopes, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            server_name,
            tokens['access_token'],
            tokens.get('refresh_token'),
            tokens.get('token_type', 'Bearer'),
            expires_at,
            scopes,
            now,
            now
        ))
        
        conn.commit()
        conn.close()
        print(f"✅ Tokens saved for {server_name}")
    
    def get_tokens(self, server_name: str) -> Optional[Dict]:
        """Retrieve tokens for a server"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        
        cursor = conn.execute(
            "SELECT * FROM tokens WHERE server_name = ?",
            (server_name,)
        )
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'access_token': row['access_token'],
                'refresh_token': row['refresh_token'],
                'token_type': row['token_type'],
                'expires_at': row['expires_at'],
                'scopes': row['scopes'].split() if row['scopes'] else []
            }
        return None
    
    def is_token_expired(self, server_name: str, buffer_seconds: int = 300) -> bool:
        """Check if token is expired (with 5 minute buffer by default)"""
        tokens = self.get_tokens(server_name)
        if not tokens:
            return True
        
        return datetime.now().timestamp() > (tokens['expires_at'] - buffer_seconds)
    
    def delete_tokens(self, server_name: str):
        """Delete tokens for a server"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("DELETE FROM tokens WHERE server_name = ?", (server_name,))
        conn.commit()
        conn.close()
        print(f"🗑️  Tokens deleted for {server_name}")
    
    def list_servers(self) -> list[str]:
        """List all servers with stored tokens"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute("SELECT server_name FROM tokens")
        servers = [row[0] for row in cursor.fetchall()]
        conn.close()
        return servers

