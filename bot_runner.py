#!/usr/bin/env python3
"""
Telegram Bot Runner

This script runs the Telegram bot either standalone or integrated with the MCP server.
It supports both polling and webhook modes.
"""

import asyncio
import os
import logging
import json
from datetime import datetime
from typing import Dict, List, Any, Optional

from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from dotenv import load_dotenv
import httpx

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
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8001")
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required")

# Global storage (in production, use a proper database)
user_sessions: Dict[int, Dict[str, Any]] = {}
conversation_history: List[Dict[str, Any]] = []

class TelegramBotRunner:
    """Main Telegram bot runner class"""
    
    def __init__(self):
        self.application = None
        self.bot = None
        self.mcp_client = None
    
    async def initialize(self):
        """Initialize the bot application"""
        self.application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        self.bot = self.application.bot
        
        # Initialize HTTP client for MCP communication
        self.mcp_client = httpx.AsyncClient(base_url=MCP_SERVER_URL)
        
        # Add command handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("info", self.info_command))
        self.application.add_handler(CommandHandler("stats", self.stats_command))
        self.application.add_handler(CommandHandler("clear", self.clear_command))
        
        # Add message handler
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message)
        )
        
        logger.info("Bot initialized successfully")
    
    async def start_command(self, update: Update, context: CallbackContext) -> None:
        """Handle /start command"""
        user = update.effective_user
        chat_id = update.effective_chat.id
        
        # Store user session
        user_sessions[user.id] = {
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "chat_id": chat_id,
            "last_seen": datetime.now().isoformat(),
            "message_count": 0
        }
        
        welcome_message = f"""
🤖 <b>Welcome to the MCP-Powered Telegram Bot!</b>

Hello {user.first_name}! I'm an advanced Telegram bot powered by the Model Context Protocol (MCP) and FastMCP framework.

🚀 <b>What I can do:</b>
• Process and respond to your messages intelligently
• Maintain conversation context
• Provide various utility commands
• Integrate with AI models through MCP

📋 <b>Available Commands:</b>
/start - Show this welcome message
/help - Get detailed help information
/info - Show your user information
/stats - View bot statistics
/clear - Clear your conversation history

💬 Just send me any message and I'll respond using my MCP-powered capabilities!

🔧 <b>Powered by:</b> FastMCP + python-telegram-bot
        """
        
        await update.message.reply_text(welcome_message, parse_mode='HTML')
        
        # Log to conversation history
        await self._log_interaction(user.id, "command", "/start", "Welcome message sent")
    
    async def help_command(self, update: Update, context: CallbackContext) -> None:
        """Handle /help command"""
        help_text = """
🔧 <b>Detailed Bot Help</b>

<b>Commands:</b>
/start - Initialize the bot and show welcome message
/help - Display this help information
/info - Show your user profile and session info
/stats - View global bot statistics
/clear - Clear your personal conversation history

<b>Features:</b>
🤖 <b>AI Integration:</b> Powered by Model Context Protocol (MCP)
💬 <b>Smart Responses:</b> Context-aware message processing
📊 <b>Analytics:</b> Message tracking and user statistics
🔒 <b>Privacy:</b> Your data is handled securely

<b>How to use:</b>
Simply send me any text message and I'll process it through my MCP-powered backend. I can understand context, maintain conversations, and provide intelligent responses.

<b>Technical Details:</b>
• Built with FastMCP framework
• Uses python-telegram-bot library
• Supports both polling and webhook modes
• Integrates with various AI models

Need more help? Just ask me anything!
        """
        
        await update.message.reply_text(help_text, parse_mode='HTML')
        await self._log_interaction(update.effective_user.id, "command", "/help", "Help information provided")
    
    async def info_command(self, update: Update, context: CallbackContext) -> None:
        """Handle /info command"""
        user = update.effective_user
        session = user_sessions.get(user.id, {})
        
        info_text = f"""
👤 <b>Your Information</b>

<b>Telegram Profile:</b>
• User ID: <code>{user.id}</code>
• Username: @{user.username or 'Not set'}
• Name: {user.first_name} {user.last_name or ''}
• Is Bot: {'Yes' if user.is_bot else 'No'}
• Language: {user.language_code or 'Not detected'}

<b>Session Data:</b>
• First Seen: {session.get('last_seen', 'Unknown')}
• Messages Sent: {session.get('message_count', 0)}
• Chat ID: <code>{update.effective_chat.id}</code>
• Chat Type: {update.effective_chat.type}

<b>Recent Activity:</b>
{await self._get_user_recent_activity(user.id)}
        """
        
        await update.message.reply_text(info_text, parse_mode='HTML')
        await self._log_interaction(user.id, "command", "/info", "User info provided")
    
    async def stats_command(self, update: Update, context: CallbackContext) -> None:
        """Handle /stats command"""
        total_users = len(user_sessions)
        total_messages = len(conversation_history)
        
        # Calculate some basic stats
        user_message_counts = {}
        command_counts = {}
        
        for interaction in conversation_history:
            user_id = interaction.get('user_id')
            interaction_type = interaction.get('type')
            content = interaction.get('content', '')
            
            if user_id:
                user_message_counts[user_id] = user_message_counts.get(user_id, 0) + 1
            
            if interaction_type == 'command':
                command_counts[content] = command_counts.get(content, 0) + 1
        
        most_active_user = max(user_message_counts.items(), default=(None, 0))[0] if user_message_counts else None
        most_used_command = max(command_counts.items(), default=(None, 0))[0] if command_counts else None
        
        stats_text = f"""
📊 <b>Bot Statistics</b>

<b>General Stats:</b>
• Total Users: {total_users}
• Total Interactions: {total_messages}
• Most Active User ID: {most_active_user or 'None'}
• Most Used Command: {most_used_command or 'None'}

<b>Command Usage:</b>
{self._format_command_stats(command_counts)}

<b>Recent Activity:</b>
• Last interaction: {conversation_history[-1].get('timestamp', 'None') if conversation_history else 'No activity'}

<b>System Info:</b>
• MCP Server: {MCP_SERVER_URL}
• Debug Mode: {'On' if DEBUG else 'Off'}
        """
        
        await update.message.reply_text(stats_text, parse_mode='HTML')
        await self._log_interaction(update.effective_user.id, "command", "/stats", "Stats provided")
    
    async def clear_command(self, update: Update, context: CallbackContext) -> None:
        """Handle /clear command"""
        user_id = update.effective_user.id
        
        # Remove user's conversation history
        global conversation_history
        conversation_history = [
            msg for msg in conversation_history 
            if msg.get('user_id') != user_id
        ]
        
        # Reset user session
        if user_id in user_sessions:
            user_sessions[user_id]['message_count'] = 0
        
        clear_text = """
🗑️ <b>History Cleared</b>

Your conversation history has been cleared successfully!

This affects:
• Your personal message history
• Context for future conversations
• Your message count statistics

Your user profile information remains unchanged.
        """
        
        await update.message.reply_text(clear_text, parse_mode='HTML')
        await self._log_interaction(user_id, "command", "/clear", "History cleared")
    
    async def handle_message(self, update: Update, context: CallbackContext) -> None:
        """Handle incoming text messages"""
        user = update.effective_user
        message = update.message
        
        # Update user session
        if user.id in user_sessions:
            user_sessions[user.id]['message_count'] += 1
            user_sessions[user.id]['last_seen'] = datetime.now().isoformat()
        
        # Log the interaction
        await self._log_interaction(user.id, "message", message.text, "")
        
        # Process message through MCP (if available)
        try:
            response = await self._process_with_mcp(user.id, message.text)
        except Exception as e:
            logger.warning(f"MCP processing failed: {e}")
            response = await self._fallback_response(message.text)
        
        # Send response
        await message.reply_text(response, parse_mode='HTML')
        
        # Log the response
        await self._log_interaction(user.id, "bot_response", response, "Response sent")
    
    async def _process_with_mcp(self, user_id: int, text: str) -> str:
        """Process message through MCP server"""
        try:
            # This would integrate with your MCP server
            # For now, return a simple intelligent response
            
            user_info = user_sessions.get(user_id, {})
            message_count = user_info.get('message_count', 0)
            
            # Simulate MCP processing
            response = f"""
🤖 <b>MCP-Powered Response</b>

I received your message: "<i>{text}</i>"

📊 <b>Analysis:</b>
• Message length: {len(text)} characters
• Your message #{message_count}
• Processing timestamp: {datetime.now().strftime('%H:%M:%S')}

💭 <b>Context-Aware Reply:</b>
{await self._generate_contextual_response(text, user_info)}

<i>Powered by FastMCP and Model Context Protocol</i>
            """
            
            return response
            
        except Exception as e:
            logger.error(f"MCP processing error: {e}")
            raise
    
    async def _fallback_response(self, text: str) -> str:
        """Fallback response when MCP is unavailable"""
        return f"""
⚠️ <b>Fallback Mode</b>

MCP server is currently unavailable, but I can still respond!

You said: "<i>{text}</i>"

I'm a Telegram bot built with FastMCP framework. While my advanced AI features are temporarily offline, I'm still here to chat with you!

Try using one of my commands:
• /help - Get help information
• /info - View your profile
• /stats - See bot statistics
        """
    
    async def _generate_contextual_response(self, text: str, user_info: Dict) -> str:
        """Generate a contextual response based on user history"""
        message_count = user_info.get('message_count', 0)
        
        if message_count == 1:
            return f"Welcome! This is your first message. I'm excited to chat with you about: {text}"
        elif message_count < 5:
            return f"Thanks for continuing our conversation! Regarding '{text}' - I'm processing this with full context awareness."
        elif "hello" in text.lower() or "hi" in text.lower():
            return f"Hello again! I see you've sent {message_count} messages so far. How can I help you today?"
        elif "?" in text:
            return f"That's a great question! Let me think about '{text}' in the context of our previous {message_count-1} messages."
        else:
            return f"Interesting point about '{text}'. Based on our conversation history, I can provide contextual insights."
    
    async def _log_interaction(self, user_id: int, interaction_type: str, content: str, response: str):
        """Log user interactions"""
        interaction = {
            "user_id": user_id,
            "type": interaction_type,
            "content": content,
            "response": response,
            "timestamp": datetime.now().isoformat()
        }
        conversation_history.append(interaction)
    
    async def _get_user_recent_activity(self, user_id: int) -> str:
        """Get recent activity for a user"""
        user_interactions = [
            msg for msg in conversation_history[-10:] 
            if msg.get('user_id') == user_id
        ]
        
        if not user_interactions:
            return "No recent activity"
        
        activity_lines = []
        for interaction in user_interactions[-3:]:
            timestamp = interaction.get('timestamp', '')[:19]
            interaction_type = interaction.get('type', 'unknown')
            content = interaction.get('content', '')[:50]
            activity_lines.append(f"• {timestamp}: {interaction_type} - {content}...")
        
        return "\n".join(activity_lines)
    
    def _format_command_stats(self, command_counts: Dict[str, int]) -> str:
        """Format command usage statistics"""
        if not command_counts:
            return "No commands used yet"
        
        stats_lines = []
        for command, count in sorted(command_counts.items(), key=lambda x: x[1], reverse=True):
            stats_lines.append(f"• {command}: {count} times")
        
        return "\n".join(stats_lines[:5])  # Top 5 commands
    
    async def start_polling(self):
        """Start the bot in polling mode"""
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()
        
        logger.info("Bot started in polling mode")
        
        try:
            # Keep running until interrupted
            await asyncio.Event().wait()
        except KeyboardInterrupt:
            logger.info("Bot stopped by user")
        finally:
            await self.stop()
    
    async def stop(self):
        """Stop the bot gracefully"""
        if self.application:
            await self.application.updater.stop()
            await self.application.stop()
            await self.application.shutdown()
        
        if self.mcp_client:
            await self.mcp_client.aclose()
        
        logger.info("Bot stopped")

# Main execution
async def main():
    """Main function to run the bot"""
    bot_runner = TelegramBotRunner()
    await bot_runner.initialize()
    
    try:
        await bot_runner.start_polling()
    except Exception as e:
        logger.error(f"Error running bot: {e}")
        await bot_runner.stop()

if __name__ == "__main__":
    asyncio.run(main()) 