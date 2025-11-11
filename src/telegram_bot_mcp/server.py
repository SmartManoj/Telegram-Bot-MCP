"""
Simple Telegram Bot MCP Server v2 using Smithery patterns

This version uses the @smithery.server decorator and session-scoped configuration
for better security and multi-user support.
"""

import requests
from mcp.server.fastmcp import Context, FastMCP
from pydantic import BaseModel, Field

from smithery.decorators import smithery


# Session-level configuration schema
class ConfigSchema(BaseModel):
    telegram_bot_token: str = Field('1234567890:ABCDEFghijklmnopqrstuvwxyz123456789', description="Your Telegram Bot Token from @BotFather")
    telegram_chat_id: str = Field('123456789', description="Your Telegram Chat ID")


@smithery.server(config_schema=ConfigSchema)
def create_server():
    """Create and configure the Telegram Bot MCP server."""
    
    server = FastMCP("Simple Telegram Bot MCP")

    @server.tool()
    def send_telegram_message(text: str, ctx: Context) -> str:
        """Send a message to a Telegram chat using the bot API."""
        try:
            # Access session-specific config through context
            session_config = ctx.session_config
            
            # Get credentials from session config
            token = session_config.telegram_bot_token
            chat_id = session_config.telegram_chat_id
            
            # Send message via Telegram API
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            rj = requests.get(url, params={'chat_id': chat_id, 'text': text}).json()
            
            if rj.get('ok'):
                return 'Message sent successfully!'
            else:
                return f"Error sending message: {rj.get('description', 'Unknown error')}"
                
        except Exception as e:
            return f"Error sending message: {str(e)}"

    @server.resource("telegram://about")
    def about_telegram() -> str:
        """Information about using this Telegram Bot MCP server."""
        return (
            "Telegram Bot MCP Server\n\n"
            "This server allows you to send messages to Telegram chats via the Telegram Bot API.\n\n"
            "Configuration Required:\n"
            "- telegram_bot_token: Get this from @BotFather on Telegram\n"
            "- telegram_chat_id: Your chat or channel ID\n\n"
            "Available Tools:\n"
            "- send_telegram_message: Send a text message to your configured chat\n\n"
            "To get started:\n"
            "1. Create a bot with @BotFather and get your bot token\n"
            "2. Get your chat ID (you can use @userinfobot)\n"
            "3. Configure these values when connecting to this server"
        )

    @server.prompt()
    def telegram_message(recipient: str, message: str) -> list:
        """Generate a prompt for sending a Telegram message."""
        return [
            {
                "role": "user",
                "content": f"Send this message to {recipient} via Telegram: {message}",
            },
        ]

    return server

