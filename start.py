"""
Unified startup script for Telegram Bot MCP

This script can start the bot in different modes:
- Polling mode (default)
- Webhook mode
- MCP server mode
- Combined mode (webhook + MCP server)
"""

import asyncio
import argparse
import logging
import sys
import subprocess
from typing import Optional
import signal
import os

from config import config
from bot_runner import TelegramBotRunner

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=getattr(logging, config.server.log_level)
)
logger = logging.getLogger(__name__)

class StartupManager:
    """Manages different startup modes for the bot"""
    
    def __init__(self):
        self.processes = []
        self.bot_runner: Optional[TelegramBotRunner] = None
        self.running = True
    
    async def start_polling_mode(self):
        """Start bot in polling mode"""
        logger.info("Starting bot in polling mode...")
        
        self.bot_runner = TelegramBotRunner()
        await self.bot_runner.initialize()
        
        try:
            await self.bot_runner.start_polling()
        except KeyboardInterrupt:
            logger.info("Received shutdown signal")
        finally:
            if self.bot_runner:
                await self.bot_runner.stop()
    
    async def start_webhook_mode(self):
        """Start bot in webhook mode using FastAPI"""
        logger.info("Starting bot in webhook mode...")
        
        if not config.telegram.webhook_url:
            raise ValueError("TELEGRAM_WEBHOOK_URL must be set for webhook mode")
        
        # Import here to avoid circular imports
        import uvicorn
        
        # Configure uvicorn
        uvicorn_config = uvicorn.Config(
            "webhook_server:app",
            host=config.server.host,
            port=config.server.port,
            log_level=config.server.log_level.lower(),
            reload=config.server.debug
        )
        
        server = uvicorn.Server(uvicorn_config)
        
        try:
            await server.serve()
        except KeyboardInterrupt:
            logger.info("Received shutdown signal")
        finally:
            if hasattr(server, 'should_exit'):
                server.should_exit = True
    
    def start_mcp_server(self):
        """Start MCP server in separate process"""
        logger.info(f"Starting MCP server on port {config.server.mcp_port}...")
        
        cmd = [
            sys.executable, "telegram_bot_mcp.py", 
            "--server", str(config.server.mcp_port)
        ]
        
        process = subprocess.Popen(
            cmd,
            text=True
        )
        
        self.processes.append(process)
        logger.info(f"MCP server started with PID {process.pid}")
        
        return process
    
    async def start_combined_mode(self):
        """Start both webhook server and MCP server"""
        logger.info("Starting combined mode (webhook + MCP server)...")
        
        # Start MCP server in background
        mcp_process = self.start_mcp_server()
        
        # Wait a bit for MCP server to start
        await asyncio.sleep(2)
        
        try:
            # Start webhook server
            await self.start_webhook_mode()
        except KeyboardInterrupt:
            logger.info("Received shutdown signal")
        finally:
            self.cleanup_processes()
    
    def cleanup_processes(self):
        """Clean up all spawned processes"""
        logger.info("Cleaning up processes...")
        
        for process in self.processes:
            if process.poll() is None:  # Still running
                logger.info(f"Terminating process {process.pid}")
                process.terminate()
                
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    logger.warning(f"Force killing process {process.pid}")
                    process.kill()
        
        self.processes.clear()
    
    def setup_signal_handlers(self):
        """Setup graceful shutdown handlers"""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}")
            self.running = False
            self.cleanup_processes()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

def create_parser():
    """Create command line argument parser"""
    parser = argparse.ArgumentParser(
        description="Telegram Bot MCP - Unified Startup Script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python start.py                    # Start in polling mode
  python start.py --webhook          # Start in webhook mode
  python start.py --mcp              # Start MCP server only
  python start.py --combined         # Start webhook + MCP server
  python start.py --polling --debug  # Start in polling mode with debug
        """
    )
    
    # Mode selection
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--polling", 
        action="store_true", 
        help="Start in polling mode (default)"
    )
    mode_group.add_argument(
        "--webhook", 
        action="store_true", 
        help="Start in webhook mode"
    )
    mode_group.add_argument(
        "--mcp", 
        action="store_true", 
        help="Start MCP server only"
    )
    mode_group.add_argument(
        "--combined", 
        action="store_true", 
        help="Start both webhook and MCP server"
    )
    
    # Configuration overrides
    parser.add_argument(
        "--host", 
        default=config.server.host,
        help=f"Server host (default: {config.server.host})"
    )
    parser.add_argument(
        "--port", 
        type=int, 
        default=config.server.port,
        help=f"Server port (default: {config.server.port})"
    )
    parser.add_argument(
        "--mcp-port", 
        type=int, 
        default=config.server.mcp_port,
        help=f"MCP server port (default: {config.server.mcp_port})"
    )
    parser.add_argument(
        "--debug", 
        action="store_true",
        help="Enable debug mode"
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default=config.server.log_level,
        help=f"Log level (default: {config.server.log_level})"
    )
    parser.add_argument(
        "--check-config",
        action="store_true",
        help="Check configuration and exit"
    )
    
    return parser

def check_configuration():
    """Check and display configuration"""
    print("🔧 Configuration Check")
    print("=" * 50)
    
    try:
        # Display configuration (with secrets masked)
        config_dict = config.to_dict()
        
        print("✅ Telegram Configuration:")
        print(f"   Bot Token: {'✅ Set' if config.telegram.bot_token else '❌ Missing'}")
        print(f"   Webhook URL: {config.telegram.webhook_url or '❌ Not set'}")
        print(f"   Use Webhook: {config.telegram.use_webhook}")
        
        print("\n✅ Server Configuration:")
        print(f"   Host: {config.server.host}")
        print(f"   Port: {config.server.port}")
        print(f"   MCP Port: {config.server.mcp_port}")
        print(f"   Debug: {config.server.debug}")
        print(f"   Log Level: {config.server.log_level}")
        
        print("\n✅ AI Configuration:")
        print(f"   OpenAI API Key: {'✅ Set' if config.ai.openai_api_key else '❌ Not set'}")
        print(f"   Anthropic API Key: {'✅ Set' if config.ai.anthropic_api_key else '❌ Not set'}")
        print(f"   Default Model: {config.ai.default_model}")
        
        # Check required dependencies
        print("\n📦 Dependencies Check:")
        try:
            import telegram
            print(f"   python-telegram-bot: ✅ {telegram.__version__}")
        except ImportError:
            print("   python-telegram-bot: ❌ Not installed")
        
        try:
            import fastmcp
            print("   fastmcp: ✅ Installed")
        except ImportError:
            print("   fastmcp: ❌ Not installed")
        
        try:
            import fastapi
            print("   fastapi: ✅ Installed")
        except ImportError:
            print("   fastapi: ❌ Not installed")
        
        print("\n🚀 Ready to start!")
        return True
        
    except Exception as e:
        print(f"\n❌ Configuration Error: {e}")
        return False

async def main():
    """Main entry point"""
    parser = create_parser()
    args = parser.parse_args()
    
    # Override configuration with command line arguments
    if args.host != config.server.host:
        config.server.host = args.host
    if args.port != config.server.port:
        config.server.port = args.port
    if args.mcp_port != config.server.mcp_port:
        config.server.mcp_port = args.mcp_port
    if args.debug:
        config.server.debug = True
    if args.log_level != config.server.log_level:
        config.server.log_level = args.log_level
        # Update logging level
        logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    # Check configuration
    if args.check_config:
        check_configuration()
        return
    
    # Create startup manager
    manager = StartupManager()
    manager.setup_signal_handlers()
    
    try:
        # Determine mode
        if args.webhook:
            await manager.start_webhook_mode()
        elif args.mcp:
            mcp_process = manager.start_mcp_server()
            # Wait for process to complete
            mcp_process.wait()
        elif args.combined:
            await manager.start_combined_mode()
        else:
            # Default to polling mode
            await manager.start_polling_mode()
    
    except KeyboardInterrupt:
        logger.info("Shutdown requested")
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        sys.exit(1)
    finally:
        manager.cleanup_processes()

if __name__ == "__main__":
    # Check if configuration is valid before starting
    if not check_configuration():
        print("\n❌ Please fix configuration issues before starting.")
        sys.exit(1)
    
    print("\n🚀 Starting Telegram Bot MCP...")
    asyncio.run(main()) 