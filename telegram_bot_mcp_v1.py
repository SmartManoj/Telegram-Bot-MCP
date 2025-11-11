#!/usr/bin/env python3
"""
Telegram Bot MCP Server using FastMCP

This MCP server provides tools and resources for managing a Telegram bot,
allowing LLMs to send messages, manage users, and interact with Telegram's API.
"""

import asyncio
import os
import json
import logging
from datetime import datetime
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict

from fastmcp import FastMCP, Context
from telegram import Bot, Update, Message
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from pydantic import BaseModel, Field
import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBHOOK_URL = os.getenv("TELEGRAM_WEBHOOK_URL")
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required")

# Global bot instance
bot_instance: Optional[Bot] = None
application: Optional[Application] = None

# Message storage (in production, use a proper database)
message_history: List[Dict[str, Any]] = []
user_data: Dict[int, Dict[str, Any]] = {}

@dataclass
class TelegramMessage:
    """Telegram message data structure"""
    message_id: int
    chat_id: int
    user_id: int
    username: Optional[str]
    first_name: Optional[str]
    text: Optional[str]
    timestamp: datetime
    message_type: str

class SendMessageRequest(BaseModel):
    """Request model for sending messages"""
    chat_id: int = Field(description="Chat ID to send message to")
    text: str = Field(description="Message text to send")
    parse_mode: Optional[str] = Field(default="HTML", description="Parse mode (HTML, Markdown, or None)")
    reply_to_message_id: Optional[int] = Field(default=None, description="Message ID to reply to")

class UserInfo(BaseModel):
    """User information model"""
    user_id: int
    username: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    is_bot: bool
    language_code: Optional[str]

# Initialize FastMCP server
mcp = FastMCP(
    "Telegram Bot MCP",
    dependencies=["python-telegram-bot>=21.0", "python-dotenv>=1.0.0", "httpx>=0.25.0"]
)

async def initialize_bot():
    """Initialize the Telegram bot"""
    global bot_instance, application
    
    if not bot_instance:
        bot_instance = Bot(token=TELEGRAM_BOT_TOKEN)
        application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        
        # Add handlers
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        logger.info("Bot initialized successfully")

async def start_command(update: Update, context) -> None:
    """Handle /start command"""
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    welcome_message = f"""
🤖 <b>Welcome to the MCP Telegram Bot!</b>

Hello {user.first_name}! I'm powered by Model Context Protocol (MCP) and can help you with various tasks.

Available commands:
/start - Show this welcome message
/help - Get help information
/info - Get your user information

You can also just send me any message and I'll respond!
    """
    
    await update.message.reply_text(welcome_message, parse_mode='HTML')
    
    # Store user data
    user_data[user.id] = {
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "chat_id": chat_id,
        "last_seen": datetime.now().isoformat()
    }

async def help_command(update: Update, context) -> None:
    """Handle /help command"""
    help_text = """
🔧 <b>Bot Commands:</b>

/start - Initialize the bot
/help - Show this help message
/info - Get your user information

<b>Features:</b>
• Send and receive messages
• User management
• Message history tracking
• MCP integration for AI interactions

This bot is built with FastMCP and integrates with various AI models through the Model Context Protocol.
    """
    
    await update.message.reply_text(help_text, parse_mode='HTML')

async def handle_message(update: Update, context) -> None:
    """Handle incoming text messages"""
    user = update.effective_user
    message = update.message
    
    # Store message in history
    msg_data = TelegramMessage(
        message_id=message.message_id,
        chat_id=message.chat_id,
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        text=message.text,
        timestamp=datetime.now(),
        message_type="text"
    )
    
    message_history.append(asdict(msg_data))
    
    # Echo the message (customize this logic as needed)
    response = f"🔄 You said: {message.text}\n\n💡 I received your message and it's been processed through MCP!"
    await message.reply_text(response)

# MCP Tools

@mcp.tool()
async def send_telegram_message(request: SendMessageRequest, ctx: Context) -> str:
    """Send a message to a Telegram chat"""
    await initialize_bot()
    
    try:
        message = await bot_instance.send_message(
            chat_id=request.chat_id,
            text=request.text,
            parse_mode=request.parse_mode,
            reply_to_message_id=request.reply_to_message_id
        )
        
        # Store sent message
        msg_data = TelegramMessage(
            message_id=message.message_id,
            chat_id=message.chat_id,
            user_id=bot_instance.id,
            username=bot_instance.username,
            first_name=bot_instance.first_name,
            text=message.text,
            timestamp=datetime.now(),
            message_type="bot_sent"
        )
        message_history.append(asdict(msg_data))
        
        ctx.info(f"Message sent to chat {request.chat_id}")
        return f"Message sent successfully. Message ID: {message.message_id}"
        
    except Exception as e:
        ctx.error(f"Failed to send message: {str(e)}")
        return f"Error sending message: {str(e)}"

@mcp.tool()
async def get_chat_info(chat_id: int, ctx: Context) -> str:
    """Get information about a Telegram chat"""
    await initialize_bot()
    
    try:
        chat = await bot_instance.get_chat(chat_id)
        
        info = {
            "id": chat.id,
            "type": chat.type,
            "title": getattr(chat, 'title', None),
            "username": getattr(chat, 'username', None),
            "first_name": getattr(chat, 'first_name', None),
            "last_name": getattr(chat, 'last_name', None),
            "description": getattr(chat, 'description', None),
            "member_count": getattr(chat, 'member_count', None)
        }
        
        ctx.info(f"Retrieved chat info for {chat_id}")
        return json.dumps(info, indent=2)
        
    except Exception as e:
        ctx.error(f"Failed to get chat info: {str(e)}")
        return f"Error getting chat info: {str(e)}"

@mcp.tool()
async def broadcast_message(text: str, parse_mode: str = "HTML", ctx: Context = None) -> str:
    """Broadcast a message to all known users"""
    await initialize_bot()
    
    if not user_data:
        return "No users found to broadcast to"
    
    sent_count = 0
    failed_count = 0
    
    for user_id, user_info in user_data.items():
        try:
            await bot_instance.send_message(
                chat_id=user_info["chat_id"],
                text=text,
                parse_mode=parse_mode
            )
            sent_count += 1
            
        except Exception as e:
            failed_count += 1
            if ctx:
                ctx.warning(f"Failed to send to user {user_id}: {str(e)}")
    
    result = f"Broadcast completed. Sent to {sent_count} users, {failed_count} failed."
    if ctx:
        ctx.info(result)
    
    return result

@mcp.tool()
async def get_bot_info(ctx: Context) -> str:
    """Get information about the bot"""
    await initialize_bot()
    
    try:
        me = await bot_instance.get_me()
        
        info = {
            "id": me.id,
            "username": me.username,
            "first_name": me.first_name,
            "is_bot": me.is_bot,
            "can_join_groups": me.can_join_groups,
            "can_read_all_group_messages": me.can_read_all_group_messages,
            "supports_inline_queries": me.supports_inline_queries
        }
        
        ctx.info("Retrieved bot information")
        return json.dumps(info, indent=2)
        
    except Exception as e:
        ctx.error(f"Failed to get bot info: {str(e)}")
        return f"Error getting bot info: {str(e)}"

# MCP Resources

@mcp.resource("telegram://messages/recent/{limit}")
async def get_recent_messages(limit: str) -> str:
    """Get recent messages from the bot"""
    try:
        limit_int = int(limit)
        recent_messages = message_history[-limit_int:] if message_history else []
        
        if not recent_messages:
            return "No messages found"
        
        formatted_messages = []
        for msg in recent_messages:
            timestamp = msg.get('timestamp', 'Unknown')
            user = msg.get('username') or msg.get('first_name', 'Unknown')
            text = msg.get('text', 'No text')
            formatted_messages.append(f"[{timestamp}] {user}: {text}")
        
        return "\n".join(formatted_messages)
        
    except ValueError:
        return f"Invalid limit: {limit}. Must be a number."

@mcp.resource("telegram://users/active")
async def get_active_users() -> str:
    """Get list of active users"""
    if not user_data:
        return "No active users found"
    
    users = []
    for user_id, data in user_data.items():
        user_info = f"User ID: {user_id}\n"
        user_info += f"  Username: {data.get('username', 'N/A')}\n"
        user_info += f"  Name: {data.get('first_name', 'N/A')} {data.get('last_name', '')}\n"
        user_info += f"  Last seen: {data.get('last_seen', 'N/A')}\n"
        users.append(user_info)
    
    return "\n".join(users)

@mcp.resource("telegram://stats/summary")
async def get_bot_stats() -> str:
    """Get bot statistics summary"""
    total_messages = len(message_history)
    total_users = len(user_data)
    
    # Count message types
    message_types = {}
    for msg in message_history:
        msg_type = msg.get('message_type', 'unknown')
        message_types[msg_type] = message_types.get(msg_type, 0) + 1
    
    stats = f"""
Bot Statistics Summary:
======================

Total Messages: {total_messages}
Total Users: {total_users}

Message Types:
{json.dumps(message_types, indent=2)}

Recent Activity:
- Last message: {message_history[-1].get('timestamp', 'N/A') if message_history else 'No messages'}
- Most active user: {max(user_data.items(), key=lambda x: x[1].get('last_seen', ''), default=('None', {}))[0] if user_data else 'None'}
"""
    
    return stats

# MCP Prompts

@mcp.prompt()
def create_welcome_message(bot_name: str, features: str) -> str:
    """Create a personalized welcome message for the bot"""
    return f"""
Create a warm, engaging welcome message for a Telegram bot named "{bot_name}".

The bot has these features: {features}

The message should:
- Be welcoming and friendly
- Explain what the bot can do
- Include relevant emojis
- Be formatted in HTML for Telegram
- Include basic usage instructions

Keep it concise but informative.
"""

@mcp.prompt()
def generate_help_content(available_commands: str) -> str:
    """Generate comprehensive help content for the bot"""
    return f"""
Create detailed help documentation for a Telegram bot with these commands: {available_commands}

The help content should:
- List all available commands with descriptions
- Provide usage examples
- Include tips for effective use
- Be well-formatted with HTML
- Use appropriate emojis for visual appeal

Make it comprehensive but easy to understand for users.
"""

# Main execution
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--server":
        # Run as MCP server
        port = int(sys.argv[2]) if len(sys.argv) > 2 else 8001
        mcp.run("streamable-http", port=port)
    else:
        # Run the Telegram bot
        async def main():
            await initialize_bot()
            await application.initialize()
            
            if WEBHOOK_URL:
                # Use webhook mode
                await application.bot.set_webhook(url=WEBHOOK_URL)
                logger.info(f"Webhook set to: {WEBHOOK_URL}")
                
                # In production, you'd typically use a web framework like FastAPI
                # to handle the webhook endpoint
                logger.info("Bot is running in webhook mode")
                
            else:
                # Use polling mode
                logger.info("Starting bot in polling mode...")
                await application.start()
                await application.updater.start_polling()
                
                try:
                    # Keep the bot running
                    await asyncio.Event().wait()
                except KeyboardInterrupt:
                    logger.info("Stopping bot...")
                finally:
                    await application.updater.stop()
                    await application.stop()
                    await application.shutdown()
        
        asyncio.run(main()) 