#!/usr/bin/env python3
"""
Configuration management for Telegram Bot MCP
"""

import os
from typing import Optional, Dict, Any
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@dataclass
class TelegramConfig:
    """Telegram bot configuration"""
    bot_token: str
    webhook_url: Optional[str] = None
    webhook_secret: Optional[str] = None
    use_webhook: bool = False
    
    @classmethod
    def from_env(cls) -> "TelegramConfig":
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required")
        
        webhook_url = os.getenv("TELEGRAM_WEBHOOK_URL")
        webhook_secret = os.getenv("WEBHOOK_SECRET")
        use_webhook = webhook_url is not None
        
        return cls(
            bot_token=bot_token,
            webhook_url=webhook_url,
            webhook_secret=webhook_secret,
            use_webhook=use_webhook
        )

@dataclass
class ServerConfig:
    """Server configuration"""
    host: str = "0.0.0.0"
    port: int = 8000
    mcp_port: int = 8001
    debug: bool = False
    log_level: str = "INFO"
    
    @classmethod
    def from_env(cls) -> "ServerConfig":
        return cls(
            host=os.getenv("SERVER_HOST", "0.0.0.0"),
            port=int(os.getenv("SERVER_PORT", 8000)),
            mcp_port=int(os.getenv("MCP_PORT", 8001)),
            debug=os.getenv("DEBUG", "false").lower() == "true",
            log_level=os.getenv("LOG_LEVEL", "INFO").upper()
        )

@dataclass
class AIConfig:
    """AI services configuration"""
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    default_model: str = "gpt-3.5-turbo"
    
    @classmethod
    def from_env(cls) -> "AIConfig":
        return cls(
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
            default_model=os.getenv("DEFAULT_AI_MODEL", "gpt-3.5-turbo")
        )

@dataclass
class AppConfig:
    """Main application configuration"""
    telegram: TelegramConfig
    server: ServerConfig
    ai: AIConfig
    
    @classmethod
    def from_env(cls) -> "AppConfig":
        return cls(
            telegram=TelegramConfig.from_env(),
            server=ServerConfig.from_env(),
            ai=AIConfig.from_env()
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            "telegram": {
                "bot_token": "***" if self.telegram.bot_token else None,
                "webhook_url": self.telegram.webhook_url,
                "use_webhook": self.telegram.use_webhook
            },
            "server": {
                "host": self.server.host,
                "port": self.server.port,
                "mcp_port": self.server.mcp_port,
                "debug": self.server.debug,
                "log_level": self.server.log_level
            },
            "ai": {
                "openai_api_key": "***" if self.ai.openai_api_key else None,
                "anthropic_api_key": "***" if self.ai.anthropic_api_key else None,
                "default_model": self.ai.default_model
            }
        }

# Global configuration instance
config = AppConfig.from_env() 