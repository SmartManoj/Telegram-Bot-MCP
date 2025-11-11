from fastmcp import Client
import asyncio

async def main():
    async with Client("http://localhost:8000/mcp") as client:
        tools = await client.list_tools()
        print(tools)
        result = await client.call_tool("send_telegram_message", {"text": "Hello, World!"})
        print(result)

if __name__ == "__main__":
    asyncio.run(main())