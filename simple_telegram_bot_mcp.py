"""
Simple Telegram Bot MCP Server using FastMCP

This is a minimal MCP server that exposes the send_message function as a tool.
"""
trigger=2
import os
import sys

import uvicorn
import requests
from fastmcp import FastMCP

token = os.getenv('TELEGRAM_BOT_TOKEN')
chat_id = os.getenv('TELEGRAM_CHAT_ID')
mcp = FastMCP("Simple Telegram Bot MCP")
url = f"https://api.telegram.org/bot{token}/sendMessage"

@mcp.tool()
def send_telegram_message(text: str) -> str:
    """Send a message to a Telegram chat using the simple send_message function"""
    try:
        requests.get(url, params={'chat_id': chat_id, 'text': text})
        return 'success'
    except Exception as e:
        return f"Error sending message: {str(e)}"

app = mcp.http_app()

# Add root route
@app.route("/")
async def index(request):
    return 'Hello, World!'

if __name__ == "__main__":
    # Run the MCP server
    # port = int(sys.argv[1]) if len(sys.argv) > 1 else int(os.getenv('PORT'))
    # mcp.run("streamable-http", host='0.0.0.0', port=port) 
    uvicorn.run('simple_telegram_bot_mcp:app', host='0.0.0.0', port=8000)
