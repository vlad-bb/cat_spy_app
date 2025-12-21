import asyncio
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def test_mcp():
    server_params = StdioServerParameters(
        command="uv",
        args=["run", "python", "-m", "src.mcp_server.server"]
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # List available tools
            tools = await session.list_tools()
            print("Available tools:")
            for tool in tools.tools:
                print(f"  - {tool.name}: {tool.description}")
            
            # Test query_cats
            result = await session.call_tool("query_cats", {"limit": 5})
            print("\n\nQuery Cats Result:")
            for content in result.content:
                print(content.text)

if __name__ == "__main__":
    asyncio.run(test_mcp())