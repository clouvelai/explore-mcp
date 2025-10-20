"""
Authentication API endpoints.
"""

import base64
import json
from flask import Blueprint, request, jsonify
from backend.auth.oauth_handler import GoogleOAuthHandler
from backend.auth.token_store import TokenStore

auth_bp = Blueprint('auth', __name__)


def setup_auth_routes(oauth_handler: GoogleOAuthHandler, token_store: TokenStore, servers_config: dict):
    """Setup auth routes with services."""
    
    @auth_bp.route('/api/oauth/start/<server_key>', methods=['GET'])
    def start_oauth(server_key):
        """Start OAuth flow for a server."""
        if server_key not in servers_config:
            return jsonify({"error": "Invalid server"}), 400
        
        server_config = servers_config[server_key]
        
        if not server_config.get("requires_auth"):
            return jsonify({"error": "Server doesn't require authentication"}), 400
        
        if server_config.get("auth_type") == "google_oauth":
            try:
                # Get authorization URL with server key in state
                auth_url, state = oauth_handler.get_authorization_url()
                
                # Encode server key into the state parameter
                state_data = {
                    "server_key": server_key,
                    "random_state": state
                }
                encoded_state = base64.b64encode(json.dumps(state_data).encode()).decode()
                
                # Replace state in URL
                auth_url = auth_url.replace(f"state={state}", f"state={encoded_state}")
                
                return jsonify({
                    "auth_url": auth_url,
                    "state": encoded_state
                })
            except Exception as e:
                return jsonify({"error": str(e)}), 500
        
        return jsonify({"error": "Unsupported auth type"}), 400

    @auth_bp.route('/api/oauth/callback', methods=['GET'])
    def oauth_callback():
        """Handle OAuth callback from Google."""
        code = request.args.get('code')
        state = request.args.get('state')
        error = request.args.get('error')
        
        if error:
            return f"""
            <html>
            <body style="font-family: sans-serif; text-align: center; padding-top: 100px;">
                <h1>❌ Authentication Failed</h1>
                <p>Error: {error}</p>
                <p><a href="http://localhost:3000">Return to chat</a></p>
            </body>
            </html>
            """
        
        if not code:
            return "No authorization code received", 400
        
        # Decode state parameter
        try:
            state_data = json.loads(base64.b64decode(state.encode()).decode())
            server_key = state_data.get('server_key')
            random_state = state_data.get('random_state')
        except Exception as e:
            return f"Invalid state parameter format: {str(e)}", 400
        
        if not server_key:
            return "No server key in state", 400
        
        try:
            # Exchange code for tokens (use the original random state)
            tokens = oauth_handler.exchange_code_for_tokens(code, random_state)
            
            # Save tokens
            token_store.save_tokens(server_key, tokens)
            
            # Return success page with auto-close
            return f"""
            <html>
            <body style="font-family: sans-serif; text-align: center; padding-top: 100px;">
                <h1>✅ Authentication Successful!</h1>
                <p>You can now use {servers_config[server_key]['name']} tools.</p>
                <p>This window will close automatically...</p>
                <script>
                    setTimeout(function() {{
                        window.close();
                    }}, 2000);
                </script>
                <p><a href="http://localhost:3000">Return to chat</a></p>
            </body>
            </html>
            """
        
        except Exception as e:
            return f"""
            <html>
            <body style="font-family: sans-serif; text-align: center; padding-top: 100px;">
                <h1>❌ Authentication Failed</h1>
                <p>Error: {str(e)}</p>
                <p><a href="http://localhost:3000">Return to chat</a></p>
            </body>
            </html>
            """

    @auth_bp.route('/api/oauth/disconnect/<server_key>', methods=['POST'])
    def disconnect_oauth(server_key):
        """Disconnect/remove authentication for a server."""
        if server_key not in servers_config:
            return jsonify({"error": "Invalid server"}), 400
        
        try:
            token_store.delete_tokens(server_key)
            return jsonify({"message": f"Disconnected from {servers_config[server_key]['name']}"})
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    return auth_bp