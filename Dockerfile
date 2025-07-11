# Simple Telegram Bot MCP - FastMCP server for Telegram bot messaging
# syntax=docker/dockerfile:1
FROM python:3.12-slim
WORKDIR /app
# Copy project files
COPY requirements.txt README.md ./
COPY *.py ./
# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt
# Ensure logging flushes immediately
ENV PYTHONUNBUFFERED=1
ENTRYPOINT ["python", "simple_telegram_bot_mcp.py"] 
