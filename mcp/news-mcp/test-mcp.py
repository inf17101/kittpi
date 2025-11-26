# test_server.py
import asyncio
from fastmcp import Client
from news_mcp import mcp

async def test_tools():
    client = Client(mcp)
    
    async with client:
        tools = await client.list_tools()
        print(f"Available tools: {tools}")
        # Test tool call
        result = await client.call_tool(
            "fetch_regional_news",
            {"regions": "1, 2", "ressort": "wirtschaft"}
        )
        print(f"News for regions '1, 2' and ressort 'wirtschaft': {result}")

        result = await client.call_tool(
            "fetch_default_news_by_ressort",
            {"region": 2}
        )
        print(f"News Top 3 per ressort: {result}")

        result = await client.call_tool(
            "fetch_article_details",
            {"details_url": "https://www.tagesschau.de/api2u/inland/lindner-wechsel-autobranche-100.json"}
        )
        print(f"Details: {result}")

if __name__ == "__main__":
    asyncio.run(test_tools())
