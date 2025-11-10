"""
Simple Telegram Bot MCP Server using FastMCP

This is a minimal MCP server that exposes the send_message function as a tool.
"""
trigger=3
import os

import requests
from fastmcp import FastMCP
from dotenv import load_dotenv
load_dotenv()
from middleware import SmitheryConfigMiddleware
chat_id = os.getenv('TELEGRAM_CHAT_ID')
token = os.getenv('TELEGRAM_BOT_TOKEN')
mcp = FastMCP("Simple Telegram Bot MCP")

def get_request_config() -> dict:
    """Get full config from current request context."""
    try:
        # Access the current request context from FastMCP
        import contextvars
        
        # Try to get from request context if available
        request = contextvars.copy_context().get('request')
        if hasattr(request, 'scope') and request.scope:
            return request.scope.get('smithery_config', {})
    except:
        pass
    
    # Return empty dict if no config found
    return {}

def get_config_value(key: str, default=None):
    """Get a specific config value from current request."""
    config = get_request_config()
    # Handle case where config might be None
    if config is None:
        config = {}
    return config.get(key, default)


@mcp.tool
def send_telegram_message(text: str) -> str:
    """Send a message to a Telegram chat using the simple send_message function"""
    try:
        chat_id = get_config_value("telegramChatId")
        token = get_config_value("telegramBotToken")
        url = f"https://api.telegram.org/bot{token}/sendMessage"

        rj = requests.get(url, params={'chat_id': chat_id, 'text': text}).json()
        if rj['ok']:
            return 'success'
        else:
            return f"Error sending message: {rj['description']}"
    except Exception as e:
        return f"Error sending message: {str(e)}"

# app = mcp.http_app()

# # Add root route
# @app.route("/")
# async def index(request):
#     return 'Hello, World!'
import uvicorn
from starlette.middleware.cors import CORSMiddleware

def main():
    transport_mode = os.getenv("TRANSPORT", "http")
    
    if transport_mode == "http":
        
        # Setup Starlette app with CORS for cross-origin requests
        app = mcp.streamable_http_app()
        
        # IMPORTANT: add CORS middleware for browser based clients
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["GET", "POST", "OPTIONS"],
            allow_headers=["*"],
            expose_headers=["mcp-session-id", "mcp-protocol-version"],
            max_age=86400,
        )

        # Apply custom middleware for session config extraction
        app = SmitheryConfigMiddleware(app)

        # Use Smithery-required PORT environment variable
        port = int(os.environ.get("PORT", 8081))
        print(f"Listening on port {port}")

        uvicorn.run(app, host="0.0.0.0", port=port, log_level="debug")
    
    else:
        # Optional: if you need backward compatibility, add stdio transport
        # You can publish this to uv for users to run locally
        print("Character Counter MCP Server starting in stdio mode...")
        
        server_token = os.getenv("SERVER_TOKEN")
        case_sensitive = os.getenv("CASE_SENSITIVE", "false").lower() == "true"
        # Set the server token and case sensitivity for stdio mode
        handle_config({"serverToken": server_token, "caseSensitive": case_sensitive})
        
        # Run with stdio transport (default)
        mcp.run()

if __name__ == "__main__":
    main()