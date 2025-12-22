"""Tool definitions and handlers for the Cat Spy MCP server."""
from mcp.types import Tool, TextContent
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text


def get_tool_definitions() -> list[Tool]:
    """Return list of all available tools."""
    return [
        Tool(
            name="query_cats",
            description="Query spy cats from the database. Returns list of cats with their details.",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Optional: Filter cats by name (partial match)"
                    },
                    "breed": {
                        "type": "string",
                        "description": "Optional: Filter cats by breed"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results (default 10)",
                        "default": 10
                    }
                }
            }
        ),
        Tool(
            name="query_missions",
            description="Query missions from the database. Returns list of missions with their details.",
            inputSchema={
                "type": "object",
                "properties": {
                    "cat_uuid": {
                        "type": "string",
                        "description": "Optional: Filter missions assigned to specific cat (UUID)"
                    },
                    "status": {
                        "type": "string",
                        "description": "Optional: Filter by status (pending, in_progress, completed, etc.)"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results (default 10)",
                        "default": 10
                    }
                }
            }
        ),
        Tool(
            name="get_cat_stats",
            description="Get statistics about a specific cat including mission count and completion rate.",
            inputSchema={
                "type": "object",
                "properties": {
                    "cat_uuid": {
                        "type": "string",
                        "description": "The UUID of the cat"
                    }
                },
                "required": ["cat_uuid"]
            }
        ),
        Tool(
            name="execute_raw_query",
            description="""Execute a raw SQL SELECT query. Use with caution. Only SELECT queries are allowed.
            
Database Schema:
- Table: cats
  Columns: uuid (UUID, PK), name, password, refresh_token, reset_token, years_of_experience, breed, salary, created_at, updated_at, is_staff
- Table: missions
  Columns: uuid (UUID, PK), name, description, status, created_at, updated_at, completed_at
- Table: targets
  Columns: uuid (UUID, PK), name, country, status, mission_uuid (FK), created_at, updated_at
- Table: mission_cats (many-to-many)
  Columns: mission_uuid, cat_uuid
- Table: targets_cats (many-to-many)
  Columns: target_uuid, cat_uuid
- Table: notes
  Columns: uuid (UUID, PK), content, cat_uuid (FK), target_uuid (FK), created_at, updated_at

Example: SELECT * FROM cats WHERE years_of_experience > 3""",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The SQL SELECT query to execute"
                    }
                },
                "required": ["query"]
            }
        )
    ]


async def query_cats(session: AsyncSession, args: dict) -> list[TextContent]:
    """Query cats from database."""
    name_filter = args.get("name", "")
    breed_filter = args.get("breed", "")
    limit = args.get("limit", 10)
    
    query = "SELECT uuid, name, years_of_experience, breed, salary FROM cats WHERE 1=1"
    params = {}
    
    if name_filter:
        query += " AND name ILIKE :name"
        params["name"] = f"%{name_filter}%"
    
    if breed_filter:
        query += " AND breed ILIKE :breed"
        params["breed"] = f"%{breed_filter}%"
    
    query += " LIMIT :limit"
    params["limit"] = limit
    
    result = await session.execute(text(query), params)
    rows = result.fetchall()
    
    if not rows:
        return [TextContent(type="text", text="No cats found matching the criteria.")]
    
    cats_data = []
    for row in rows:
        cats_data.append({
            "uuid": str(row[0]),
            "name": row[1],
            "years_of_experience": row[2],
            "breed": row[3],
            "salary": float(row[4]) if row[4] else None
        })
    
    return [TextContent(
        type="text",
        text=f"Found {len(cats_data)} cat(s):\n\n{format_results(cats_data)}"
    )]


async def query_missions(session: AsyncSession, args: dict) -> list[TextContent]:
    """Query missions from database."""
    cat_uuid = args.get("cat_uuid")
    status = args.get("status")
    limit = args.get("limit", 10)
    
    query = """
        SELECT m.uuid, m.name, m.description, m.status, m.completed_at, COUNT(t.uuid) as target_count
        FROM missions m
        LEFT JOIN targets t ON m.uuid = t.mission_uuid
    """
    
    conditions = []
    params = {}
    
    if cat_uuid is not None:
        query += " LEFT JOIN mission_cats mc ON m.uuid = mc.mission_uuid"
        conditions.append("mc.cat_uuid = :cat_uuid::uuid")
        params["cat_uuid"] = cat_uuid
    
    if status is not None:
        conditions.append("m.status = :status")
        params["status"] = status
    
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    
    query += " GROUP BY m.uuid LIMIT :limit"
    params["limit"] = limit
    
    result = await session.execute(text(query), params)
    rows = result.fetchall()
    
    if not rows:
        return [TextContent(type="text", text="No missions found matching the criteria.")]
    
    missions_data = []
    for row in rows:
        missions_data.append({
            "uuid": str(row[0]),
            "name": row[1],
            "description": row[2],
            "status": row[3],
            "completed_at": str(row[4]) if row[4] else None,
            "target_count": row[5]
        })
    
    return [TextContent(
        type="text",
        text=f"Found {len(missions_data)} mission(s):\n\n{format_results(missions_data)}"
    )]


async def get_cat_stats(session: AsyncSession, args: dict) -> list[TextContent]:
    """Get statistics for a specific cat."""
    cat_uuid = args["cat_uuid"]
    
    # Get cat info
    cat_query = "SELECT name, breed, years_of_experience FROM cats WHERE uuid = :cat_uuid::uuid"
    cat_result = await session.execute(text(cat_query), {"cat_uuid": cat_uuid})
    cat_row = cat_result.fetchone()
    
    if not cat_row:
        return [TextContent(type="text", text=f"Cat with UUID {cat_uuid} not found.")]
    
    # Get mission stats
    stats_query = """
        SELECT 
            COUNT(*) as total_missions,
            SUM(CASE WHEN m.status = 'completed' THEN 1 ELSE 0 END) as completed_missions
        FROM mission_cats mc
        JOIN missions m ON mc.mission_uuid = m.uuid
        WHERE mc.cat_uuid = :cat_uuid::uuid
    """
    stats_result = await session.execute(text(stats_query), {"cat_uuid": cat_uuid})
    stats_row = stats_result.fetchone()
    
    total_missions = stats_row[0] if stats_row else 0
    completed_missions = stats_row[1] if stats_row else 0
    completion_rate = (completed_missions / total_missions * 100) if total_missions > 0 else 0
    
    result_text = f"""
Cat Statistics for: {cat_row[0]}
--------------------------------
Breed: {cat_row[1]}
Experience: {cat_row[2]} years
Total Missions: {total_missions}
Completed Missions: {completed_missions}
Completion Rate: {completion_rate:.1f}%
"""
    
    return [TextContent(type="text", text=result_text)]


async def execute_raw_query(session: AsyncSession, args: dict) -> list[TextContent]:
    """Execute a raw SQL query (SELECT only)."""
    query = args["query"].strip()
    
    # Security check - only allow SELECT queries
    if not query.upper().startswith("SELECT"):
        return [TextContent(
            type="text",
            text="Error: Only SELECT queries are allowed for security reasons."
        )]
    
    result = await session.execute(text(query))
    rows = result.fetchall()
    
    if not rows:
        return [TextContent(type="text", text="Query executed successfully. No results returned.")]
    
    # Convert to list of dicts
    column_names = result.keys()
    results = []
    for row in rows:
        row_dict = dict(zip(column_names, row))
        # Convert UUIDs to strings for display
        for key, value in row_dict.items():
            if hasattr(value, 'hex'):  # Check if it's a UUID
                row_dict[key] = str(value)
        results.append(row_dict)
    
    return [TextContent(
        type="text",
        text=f"Query executed successfully. {len(results)} row(s) returned:\n\n{format_results(results)}"
    )]


def format_results(data: list) -> str:
    """Format results as readable text."""
    if not data:
        return "No data"
    
    result = []
    for i, item in enumerate(data, 1):
        result.append(f"{i}. {item}")
    
    return "\n".join(result)