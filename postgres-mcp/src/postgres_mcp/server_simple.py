#!/usr/bin/env python3
"""PostgreSQL MCP Server - Simplified version following docker-mcp pattern"""
import asyncio
import signal
import sys
import os
from typing import List, Dict, Any
import mcp.types as types
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
import mcp.server.stdio

# Add parent directory to path to import handlers
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from handlers import PostgresHandlers

# Create server instance
server = Server("postgres-mcp")

@server.list_tools()
async def handle_list_tools() -> List[types.Tool]:
    """List available PostgreSQL tools."""
    return [
        types.Tool(
            name="test-connection",
            description="Test PostgreSQL database connection",
            inputSchema={
                "type": "object",
                "properties": {
                    "database_url": {
                        "type": "string",
                        "description": "PostgreSQL connection string (optional, uses DATABASE_URI env if not provided)"
                    }
                },
                "required": []
            }
        ),
        types.Tool(
            name="list-schemas",
            description="List all schemas in the database",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        types.Tool(
            name="list-tables",
            description="List all tables in a schema",
            inputSchema={
                "type": "object",
                "properties": {
                    "schema": {
                        "type": "string",
                        "description": "Schema name (default: public)",
                        "default": "public"
                    }
                },
                "required": []
            }
        ),
        types.Tool(
            name="execute-query",
            description="Execute a SQL query",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "SQL query to execute"
                    }
                },
                "required": ["query"]
            }
        ),
        types.Tool(
            name="explain-query",
            description="Analyze query execution plan using EXPLAIN",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "SQL query to analyze"
                    },
                    "analyze": {
                        "type": "boolean",
                        "description": "Include actual execution statistics (runs the query)",
                        "default": False
                    },
                    "buffers": {
                        "type": "boolean",
                        "description": "Include buffer usage statistics",
                        "default": False
                    },
                    "format": {
                        "type": "string",
                        "description": "Output format: text, json, xml, yaml",
                        "default": "text",
                        "enum": ["text", "json", "xml", "yaml"]
                    }
                },
                "required": ["query"]
            }
        ),
        types.Tool(
            name="get-slow-queries",
            description="Get slow queries from pg_stat_statements extension",
            inputSchema={
                "type": "object",
                "properties": {
                    "min_duration_ms": {
                        "type": "number",
                        "description": "Minimum mean execution time in milliseconds",
                        "default": 1000
                    },
                    "limit": {
                        "type": "number",
                        "description": "Maximum number of queries to return",
                        "default": 20
                    }
                },
                "required": []
            }
        ),
        types.Tool(
            name="health-check",
            description="Comprehensive health check of PostgreSQL database",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        types.Tool(
            name="suggest-indexes",
            description="Analyze query workload and suggest optimal indexes",
            inputSchema={
                "type": "object",
                "properties": {
                    "min_calls": {
                        "type": "number",
                        "description": "Minimum number of calls to consider a query",
                        "default": 10
                    },
                    "min_duration_ms": {
                        "type": "number",
                        "description": "Minimum average duration in milliseconds",
                        "default": 100
                    },
                    "limit": {
                        "type": "number",
                        "description": "Maximum number of queries to analyze",
                        "default": 10
                    }
                },
                "required": []
            }
        ),
        types.Tool(
            name="get-table-stats",
            description="Get detailed statistics for database tables",
            inputSchema={
                "type": "object",
                "properties": {
                    "schema": {
                        "type": "string",
                        "description": "Schema name",
                        "default": "public"
                    },
                    "table_pattern": {
                        "type": "string",
                        "description": "SQL LIKE pattern for table names",
                        "default": "%"
                    },
                    "include_toast": {
                        "type": "boolean",
                        "description": "Include TOAST table information",
                        "default": False
                    },
                    "include_indexes": {
                        "type": "boolean",
                        "description": "Include detailed index information",
                        "default": True
                    }
                },
                "required": []
            }
        ),
        types.Tool(
            name="analyze-index-usage",
            description="Analyze index usage and identify unused or redundant indexes",
            inputSchema={
                "type": "object",
                "properties": {
                    "schema": {
                        "type": "string",
                        "description": "Schema name",
                        "default": "public"
                    },
                    "min_size_mb": {
                        "type": "number",
                        "description": "Minimum index size in MB to consider",
                        "default": 1
                    },
                    "days_unused": {
                        "type": "number",
                        "description": "Days without use to flag as unused",
                        "default": 30
                    }
                },
                "required": []
            }
        ),
        types.Tool(
            name="get-blocking-queries",
            description="Detect queries that are blocking other queries",
            inputSchema={
                "type": "object",
                "properties": {
                    "include_locks": {
                        "type": "boolean",
                        "description": "Include detailed lock information",
                        "default": True
                    },
                    "min_duration_ms": {
                        "type": "number",
                        "description": "Minimum duration for long-running queries",
                        "default": 1000
                    }
                },
                "required": []
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any] | None) -> List[types.TextContent]:
    """Handle tool execution."""
    try:
        if name == "test-connection":
            return await PostgresHandlers.handle_test_connection(arguments)
        elif name == "list-schemas":
            return await PostgresHandlers.handle_list_schemas(arguments)
        elif name == "list-tables":
            return await PostgresHandlers.handle_list_tables(arguments)
        elif name == "execute-query":
            return await PostgresHandlers.handle_execute_query(arguments)
        elif name == "explain-query":
            return await PostgresHandlers.handle_explain_query(arguments)
        elif name == "get-slow-queries":
            return await PostgresHandlers.handle_get_slow_queries(arguments)
        elif name == "health-check":
            return await PostgresHandlers.handle_health_check(arguments)
        elif name == "suggest-indexes":
            return await PostgresHandlers.handle_suggest_indexes(arguments)
        elif name == "get-table-stats":
            return await PostgresHandlers.handle_get_table_stats(arguments)
        elif name == "analyze-index-usage":
            return await PostgresHandlers.handle_analyze_index_usage(arguments)
        elif name == "get-blocking-queries":
            return await PostgresHandlers.handle_get_blocking_queries(arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")
    except Exception as e:
        return [types.TextContent(
            type="text",
            text=f"Error: {str(e)}"
        )]

async def main():
    """Main entry point."""
    # Setup signal handlers
    def handle_shutdown(signum, frame):
        sys.exit(0)
    
    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)
    
    # Get database URI (no prints to stdout!)
    db_url = os.environ.get("DATABASE_URI", "Not configured")
    
    # Run the server
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="postgres-mcp",
                server_version="0.1.0-simple",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())