#!/usr/bin/env python3
"""
Telegram Bot Webhook Server using FastAPI

This server handles Telegram webhooks and integrates with the MCP server
for production deployment.
"""

import os
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
import uvicorn
from telegram import Bot, Update
from telegram.ext import Application
from dotenv import load_dotenv
import httpx

# Import our bot logic
from bot_runner import TelegramBotRunner

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
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "your-secret-key")
SERVER_HOST = os.getenv("SERVER_HOST", "0.0.0.0")
SERVER_PORT = int(os.getenv("SERVER_PORT", 8000))
MCP_PORT = int(os.getenv("MCP_PORT", 8001))

if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required")

# Initialize FastAPI app
app = FastAPI(
    title="Telegram Bot MCP Webhook Server",
    description="Production webhook server for Telegram bot with MCP integration",
    version="1.0.0"
)

# Global instances
bot_runner: Optional[TelegramBotRunner] = None
application: Optional[Application] = None
mcp_client: Optional[httpx.AsyncClient] = None

@app.on_event("startup")
async def startup_event():
    """Initialize the bot and MCP client on startup"""
    global bot_runner, application, mcp_client
    
    logger.info("Starting webhook server...")
    
    # Initialize bot runner
    bot_runner = TelegramBotRunner()
    await bot_runner.initialize()
    application = bot_runner.application
    
    # Initialize MCP client
    mcp_client = httpx.AsyncClient(
        base_url=f"http://localhost:{MCP_PORT}",
        timeout=httpx.Timeout(30.0)
    )
    
    # Initialize the application
    await application.initialize()
    
    logger.info("Webhook server initialized successfully")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on shutdown"""
    global application, mcp_client
    
    logger.info("Shutting down webhook server...")
    
    if application:
        await application.shutdown()
    
    if mcp_client:
        await mcp_client.aclose()
    
    logger.info("Webhook server shutdown complete")

@app.get("/")
async def root():
    """Root endpoint with server information"""
    return {
        "service": "Telegram Bot MCP Webhook Server",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "webhook": "/webhook",
            "health": "/health",
            "bot_info": "/bot/info",
            "mcp_status": "/mcp/status"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check bot status
        bot_status = "ok" if application and application.bot else "error"
        
        # Check MCP status
        mcp_status = "unknown"
        if mcp_client:
            try:
                response = await mcp_client.get("/health", timeout=5.0)
                mcp_status = "ok" if response.status_code == 200 else "error"
            except:
                mcp_status = "offline"
        
        return {
            "status": "healthy" if bot_status == "ok" else "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "services": {
                "telegram_bot": bot_status,
                "mcp_server": mcp_status
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail="Health check failed")

@app.post("/webhook")
async def webhook(request: Request, background_tasks: BackgroundTasks):
    """Handle Telegram webhook updates"""
    try:
        # Get the update data
        update_data = await request.json()
        
        # Verify webhook (optional, but recommended for production)
        # You can implement signature verification here
        
        # Create Update object
        update = Update.de_json(update_data, application.bot)
        
        if update:
            # Process update in background
            background_tasks.add_task(process_update, update)
            
            return JSONResponse(
                content={"status": "ok", "message": "Update received"},
                status_code=200
            )
        else:
            logger.warning("Received invalid update data")
            return JSONResponse(
                content={"status": "error", "message": "Invalid update"},
                status_code=400
            )
    
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        raise HTTPException(status_code=500, detail="Webhook processing failed")

async def process_update(update: Update):
    """Process a Telegram update"""
    try:
        # Process the update through the application
        await application.process_update(update)
        
        # Log the update for monitoring
        if update.message:
            user_id = update.message.from_user.id if update.message.from_user else "unknown"
            text = update.message.text or "non-text message"
            logger.info(f"Processed message from user {user_id}: {text[:50]}...")
        
    except Exception as e:
        logger.error(f"Error processing update: {e}")

@app.get("/bot/info")
async def get_bot_info():
    """Get bot information"""
    try:
        if not application or not application.bot:
            raise HTTPException(status_code=503, detail="Bot not initialized")
        
        me = await application.bot.get_me()
        
        return {
            "bot_info": {
                "id": me.id,
                "username": me.username,
                "first_name": me.first_name,
                "is_bot": me.is_bot,
                "can_join_groups": me.can_join_groups,
                "can_read_all_group_messages": me.can_read_all_group_messages,
                "supports_inline_queries": me.supports_inline_queries
            },
            "webhook_info": await get_webhook_info()
        }
    
    except Exception as e:
        logger.error(f"Error getting bot info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def get_webhook_info():
    """Get webhook information"""
    try:
        webhook_info = await application.bot.get_webhook_info()
        return {
            "url": webhook_info.url,
            "has_custom_certificate": webhook_info.has_custom_certificate,
            "pending_update_count": webhook_info.pending_update_count,
            "last_error_date": webhook_info.last_error_date.isoformat() if webhook_info.last_error_date else None,
            "last_error_message": webhook_info.last_error_message,
            "max_connections": webhook_info.max_connections,
            "allowed_updates": webhook_info.allowed_updates
        }
    except Exception as e:
        logger.warning(f"Could not get webhook info: {e}")
        return {"error": str(e)}

@app.get("/mcp/status")
async def get_mcp_status():
    """Get MCP server status"""
    try:
        if not mcp_client:
            return {"status": "not_initialized"}
        
        # Try to ping the MCP server
        response = await mcp_client.get("/", timeout=5.0)
        
        if response.status_code == 200:
            return {
                "status": "connected",
                "server_url": str(mcp_client.base_url),
                "response_time": response.elapsed.total_seconds()
            }
        else:
            return {
                "status": "error",
                "status_code": response.status_code
            }
    
    except httpx.TimeoutException:
        return {"status": "timeout"}
    except httpx.ConnectError:
        return {"status": "connection_failed"}
    except Exception as e:
        return {"status": "error", "details": str(e)}

@app.post("/mcp/tool/{tool_name}")
async def call_mcp_tool(tool_name: str, request: Request):
    """Proxy tool calls to MCP server"""
    try:
        if not mcp_client:
            raise HTTPException(status_code=503, detail="MCP client not initialized")
        
        # Forward the request to MCP server
        data = await request.json()
        response = await mcp_client.post(f"/tools/{tool_name}", json=data)
        
        return response.json()
    
    except Exception as e:
        logger.error(f"MCP tool call error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/admin/set_webhook")
async def set_webhook(webhook_url: str, secret_token: Optional[str] = None):
    """Set the webhook URL for the bot (admin endpoint)"""
    try:
        if not application or not application.bot:
            raise HTTPException(status_code=503, detail="Bot not initialized")
        
        await application.bot.set_webhook(
            url=webhook_url,
            secret_token=secret_token or WEBHOOK_SECRET
        )
        
        return {
            "status": "success",
            "message": f"Webhook set to: {webhook_url}",
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error setting webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/admin/delete_webhook")
async def delete_webhook():
    """Delete the webhook (admin endpoint)"""
    try:
        if not application or not application.bot:
            raise HTTPException(status_code=503, detail="Bot not initialized")
        
        await application.bot.delete_webhook()
        
        return {
            "status": "success",
            "message": "Webhook deleted",
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error deleting webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats")
async def get_stats():
    """Get server and bot statistics"""
    try:
        # Get basic stats from bot_runner if available
        stats = {
            "server": {
                "uptime": "unknown",  # You could track this
                "requests_processed": "unknown",
                "timestamp": datetime.now().isoformat()
            },
            "bot": {
                "status": "running" if application else "stopped"
            },
            "mcp": await get_mcp_status()
        }
        
        return stats
    
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Main execution
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Telegram Bot Webhook Server")
    parser.add_argument("--host", default=SERVER_HOST, help="Server host")
    parser.add_argument("--port", type=int, default=SERVER_PORT, help="Server port")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    parser.add_argument("--log-level", default="info", help="Log level")
    
    args = parser.parse_args()
    
    logger.info(f"Starting webhook server on {args.host}:{args.port}")
    
    uvicorn.run(
        "webhook_server:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level=args.log_level,
        access_log=True
    ) 