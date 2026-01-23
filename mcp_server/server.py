"""Main MCP server implementation."""
import asyncio
import logging
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

from tools import (
    get_tool_definitions,
    query_cats,
    query_missions,
    get_cat_stats,
    execute_raw_query
)
from src.config.config import config


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database connection
DATABASE_URL = config.url
engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Initialize MCP server
app = Server("cat-spy-mcp")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available database tools."""
    return get_tool_definitions()


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls."""
    try:
        async with AsyncSessionLocal() as session:
            if name == "query_cats":
                return await query_cats(session, arguments)
            elif name == "query_missions":
                return await query_missions(session, arguments)
            elif name == "get_cat_stats":
                return await get_cat_stats(session, arguments)
            elif name == "execute_raw_query":
                return await execute_raw_query(session, arguments)
            else:
                return [TextContent(type="text", text=f"Unknown tool: {name}")]
    except Exception as e:
        logger.error(f"Error in tool {name}: {str(e)}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())