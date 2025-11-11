# Telegram Bot MCP
[![smithery badge](https://smithery.ai/badge/@SmartManoj/telegram-bot-mcp)](https://smithery.ai/server/@SmartManoj/telegram-bot-mcp)

A Telegram bot powered by FastMCP (Model Context Protocol) that enables AI integration and bot functionality. Available in both simple and full-featured variants to suit different use cases.

---

## 📦 Smithery Deployment

You can install this MCP server via [Smithery](https://smithery.ai/server/@SmartManoj/telegram-bot-mcp):

```bash
npx @smithery/cli install @SmartManoj/telegram-bot-mcp --client claude
```

# 🚀 Simple Telegram Bot MCP (`simple_telegram_bot_mcp.py`)

**Perfect for basic message sending and simple integrations**

## ✨ Features
- **Minimal Setup**: Single file with just message sending functionality
- **FastMCP Server**: Exposes `send_telegram_message` tool via MCP protocol
- **Lightweight**: Perfect for basic notification needs and simple integrations
- **Quick Start**: Requires only bot token and chat ID to get started
- **Streamable HTTP**: Runs on configurable port with streamable HTTP transport

## 📋 Requirements (Simple Version)
- Python 3.10+
- Telegram Bot Token (from [@BotFather](https://t.me/botfather))
- Chat ID where messages will be sent

## 🛠️ Installation (Simple Version)

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-username/telegram-bot-mcp.git
   cd telegram-bot-mcp
   ```

2. **Install dependencies**:
   ```bash
   pip install fastmcp python-dotenv requests
   ```

3. **Set up environment variables**:
   ```env
   TELEGRAM_BOT_TOKEN=your_bot_token_here
   TELEGRAM_CHAT_ID=your_chat_id_here
   ```

## 🚀 Quick Start (Simple Version)

```bash
# Run simple MCP server on default port 8001
python simple_telegram_bot_mcp.py

# Run on custom port
python simple_telegram_bot_mcp.py 8002
```

## 🔧 MCP Tool (Simple Version)

The simple bot exposes one MCP tool:

- `send_telegram_message(text: str)`: Send a message to the configured Telegram chat

## 🐳 Docker Usage (Simple Version)

```bash
# Build image
docker build -t simple-telegram-bot-mcp .

# Run container
docker run -e TELEGRAM_BOT_TOKEN=your_token -e TELEGRAM_CHAT_ID=your_chat_id simple-telegram-bot-mcp
```

---

# 🏢 Full-Featured Telegram Bot MCP (`telegram_bot_mcp.py`)

**Complete solution with advanced features and production capabilities**

## 🚀 Features (Full Version)
- **FastMCP Integration**: Built with FastMCP framework for seamless AI model integration
- **Multiple Deployment Modes**: Supports polling, webhook, and combined modes
- **MCP Tools & Resources**: Expose Telegram functionality as MCP tools and resources
- **AI-Powered Responses**: Context-aware intelligent responses
- **User Management**: Track users, sessions, and conversation history
- **Production Ready**: FastAPI webhook server for production deployment
- **Comprehensive Logging**: Detailed logging and monitoring capabilities
- **Flexible Configuration**: Environment-based configuration management

## 📋 Requirements (Full Version)

- Python 3.10+
- Telegram Bot Token (from [@BotFather](https://t.me/botfather))
- Optional: AI API keys (OpenAI, Anthropic) for enhanced features

## 🛠️ Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-username/telegram-bot-mcp.git
   cd telegram-bot-mcp
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   ```bash
   cp env.example .env
   # Edit .env file with your configuration
   ```

4. **Configure your bot token**:
   - Create a bot with [@BotFather](https://t.me/botfather)
   - Copy the token to your `.env` file

## ⚙️ Configuration

Create a `.env` file based on `env.example`:

```env
# Required
TELEGRAM_BOT_TOKEN=your_bot_token_here

# Optional - for webhook mode
TELEGRAM_WEBHOOK_URL=https://your-domain.com/webhook

# Server settings
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
MCP_PORT=8001

# Optional - for AI features
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here

# Debug settings
DEBUG=false
LOG_LEVEL=INFO
```

## 🚀 Quick Start

### Method 1: Using the Unified Starter (Recommended)

```bash
# Check configuration
python start.py --check-config

# Start in polling mode (default)
python start.py

# Start in webhook mode
python start.py --webhook

# Start MCP server only
python start.py --mcp

# Start both webhook and MCP server
python start.py --combined
```

### Method 2: Individual Components

```bash
# Run bot in polling mode
python bot_runner.py

# Run webhook server
python webhook_server.py

# Run MCP server
python telegram_bot_mcp.py --server
```

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Telegram      │    │   FastAPI        │    │   FastMCP       │
│   Bot API       │◄──►│   Webhook        │◄──►│   Server        │
│                 │    │   Server         │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                         │
                                ▼                         ▼
                       ┌──────────────────┐    ┌─────────────────┐
                       │   Bot Runner     │    │   AI Models     │
                       │   (Handlers)     │    │   (OpenAI, etc) │
                       └──────────────────┘    └─────────────────┘
```

## 📂 Project Structure

```
telegram-bot-mcp/
├── telegram_bot_mcp.py    # Main FastMCP server
├── bot_runner.py          # Telegram bot logic
├── webhook_server.py      # FastAPI webhook server
├── start.py              # Unified startup script
├── config.py             # Configuration management
├── requirements.txt      # Python dependencies
├── env.example          # Environment variables template
├── README.md            # This file
└── .gitattributes       # Git configuration
```

## 🔧 MCP Integration

This bot exposes several MCP tools and resources:

### Tools

- `send_telegram_message`: Send messages to Telegram chats
- `get_chat_info`: Get information about Telegram chats
- `broadcast_message`: Send messages to all known users
- `get_bot_info`: Get bot information and capabilities

### Resources

- `telegram://messages/recent/{limit}`: Get recent messages
- `telegram://users/active`: Get list of active users
- `telegram://stats/summary`: Get bot statistics

### Prompts

- `create_welcome_message`: Generate welcome messages
- `generate_help_content`: Create help documentation

## 🤖 Bot Commands

- `/start` - Initialize bot and show welcome message
- `/help` - Display help information
- `/info` - Show user profile and session info
- `/stats` - View bot statistics
- `/clear` - Clear conversation history

## 🌐 Deployment

### Development (Polling Mode)

```bash
python start.py --polling --debug
```

### Production (Webhook Mode)

1. **Set up your domain and SSL certificate**
2. **Configure webhook URL**:
   ```bash
   export TELEGRAM_WEBHOOK_URL=https://your-domain.com/webhook
   ```
3. **Start the server**:
   ```bash
   python start.py --webhook
   ```

### Docker Deployment (Optional)

Create a `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "start.py", "--webhook"]
```

Required configuration:
- `telegramBotToken`: Your Telegram Bot API token from @BotFather
- `telegramChatId`: The chat ID where messages will be sent

## 🔍 API Endpoints

When running in webhook mode, the following endpoints are available:

- `GET /` - Server information
- `GET /health` - Health check
- `POST /webhook` - Telegram webhook
- `GET /bot/info` - Bot information
- `GET /mcp/status` - MCP server status
- `GET /stats` - Server statistics

## 📊 Monitoring

The bot provides comprehensive logging and monitoring:

- **Health checks**: `/health` endpoint
- **Statistics**: User activity, message counts, command usage
- **Logging**: Structured logging with configurable levels
- **Error tracking**: Detailed error reporting

## 🛡️ Security

- **Webhook verification**: Optional signature verification
- **Environment variables**: Secure configuration management
- **Input validation**: Pydantic models for data validation
- **Error handling**: Graceful error handling and logging

## 🔧 Customization

### Adding New Commands

Edit `bot_runner.py` and add new command handlers:

```python
@self.application.add_handler(CommandHandler("mycommand", self.my_command))

async def my_command(self, update: Update, context: CallbackContext):
    await update.message.reply_text("Hello from my command!")
```

### Adding MCP Tools

Edit `telegram_bot_mcp.py` and add new tools:

```python
@mcp.tool()
async def my_tool(param: str, ctx: Context) -> str:
    """My custom tool"""
    return f"Processed: {param}"
```

### Custom AI Integration

The bot can be integrated with various AI models through the MCP protocol. Add your AI processing logic in the `_process_with_mcp` method.

## 🐛 Troubleshooting

### Common Issues

1. **Bot token not working**:
   - Verify token with [@BotFather](https://t.me/botfather)
   - Check `.env` file configuration

2. **Webhook not receiving updates**:
   - Verify webhook URL is accessible
   - Check SSL certificate
   - Review server logs

3. **MCP server connection issues**:
   - Ensure MCP server is running
   - Check port configuration
   - Verify firewall settings

### Debug Mode

Enable debug mode for detailed logging:

```bash
python start.py --debug --log-level DEBUG
```

## 📝 Logging

Logs are structured and include:

- Timestamp
- Log level
- Component name
- Message details

Configure logging level via environment variable:

```env
LOG_LEVEL=DEBUG  # DEBUG, INFO, WARNING, ERROR
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## 📜 License

This project is licensed under the MIT License. See LICENSE file for details.

## 🙏 Acknowledgments

- [FastMCP](https://github.com/jlowin/fastmcp) - FastMCP framework
- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) - Telegram Bot API wrapper
- [FastAPI](https://fastapi.tiangolo.com/) - Modern web framework

---

**Built with ❤️ using FastMCP and Python**