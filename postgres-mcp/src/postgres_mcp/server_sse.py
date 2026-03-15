#!/usr/bin/env python3
"""
PostgreSQL MCP Server with SSE (Server-Sent Events) transport
Implements the Model Context Protocol specification
"""

import argparse
import asyncio
import json
import logging
import os
import signal
import sys
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from aiohttp import web
from aiohttp_sse import sse_response

from .sql import DbConnPool, SqlDriver, SafeSqlDriver, obfuscate_password

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global database connection
db_connection = DbConnPool()

# Active SSE connections
active_connections: Dict[str, web.StreamResponse] = {}

# MCP Protocol version
PROTOCOL_VERSION = "2024-11-05"


class MCPServer:
    """MCP Server implementing the SSE transport"""
    
    def __init__(self):
        self.server_info = {
            "name": "postgres-mcp",
            "version": "1.0.0"
        }
        self.capabilities = {
            "tools": {}
        }
        self.tools = {}
        self._setup_tools()
        
    def _setup_tools(self):
        """Register available tools"""
        # Test connection tool
        self.tools["test-connection"] = {
            "description": "Test PostgreSQL database connection",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "database_url": {
                        "type": "string",
                        "description": "PostgreSQL connection string (optional, uses DATABASE_URI env if not provided)"
                    }
                },
                "required": []
            }
        }
        
        # List schemas tool
        self.tools["list-schemas"] = {
            "description": "List all schemas in the database",
            "inputSchema": {
                "type": "object",
                "properties": {}
            }
        }
        
        # List tables tool
        self.tools["list-tables"] = {
            "description": "List all tables in a schema",
            "inputSchema": {
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
        }
        
        # Execute query tool
        self.tools["execute-query"] = {
            "description": "Execute a SQL query",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "SQL query to execute"
                    }
                },
                "required": ["query"]
            }
        }
        
        # Explain query tool
        self.tools["explain-query"] = {
            "description": "Analyze query execution plan using EXPLAIN",
            "inputSchema": {
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
                        "enum": ["text", "json", "xml", "yaml"],
                        "default": "text"
                    }
                },
                "required": ["query"]
            }
        }
        
        # Get slow queries tool
        self.tools["get-slow-queries"] = {
            "description": "Get slow queries from pg_stat_statements extension",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "number",
                        "description": "Maximum number of queries to return",
                        "default": 20
                    },
                    "min_duration_ms": {
                        "type": "number",
                        "description": "Minimum mean execution time in milliseconds",
                        "default": 1000
                    }
                },
                "required": []
            }
        }
        
        # Health check tool
        self.tools["health-check"] = {
            "description": "Comprehensive health check of PostgreSQL database",
            "inputSchema": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
        
        # Suggest indexes tool
        self.tools["suggest-indexes"] = {
            "description": "Analyze query workload and suggest optimal indexes",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "number",
                        "description": "Maximum number of queries to analyze",
                        "default": 10
                    },
                    "min_calls": {
                        "type": "number",
                        "description": "Minimum number of calls to consider a query",
                        "default": 10
                    },
                    "min_duration_ms": {
                        "type": "number",
                        "description": "Minimum average duration in milliseconds",
                        "default": 100
                    }
                },
                "required": []
            }
        }
        
        # Get table stats tool
        self.tools["get-table-stats"] = {
            "description": "Get detailed statistics for database tables",
            "inputSchema": {
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
                    "include_indexes": {
                        "type": "boolean",
                        "description": "Include detailed index information",
                        "default": True
                    },
                    "include_toast": {
                        "type": "boolean",
                        "description": "Include TOAST table information",
                        "default": False
                    }
                },
                "required": []
            }
        }
        
        # Analyze index usage tool
        self.tools["analyze-index-usage"] = {
            "description": "Analyze index usage and identify unused or redundant indexes",
            "inputSchema": {
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
        }
        
        # Get blocking queries tool
        self.tools["get-blocking-queries"] = {
            "description": "Detect queries that are blocking other queries",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "min_duration_ms": {
                        "type": "number",
                        "description": "Minimum duration for long-running queries",
                        "default": 1000
                    },
                    "include_locks": {
                        "type": "boolean",
                        "description": "Include detailed lock information",
                        "default": True
                    }
                },
                "required": []
            }
        }
    
    async def handle_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming JSON-RPC messages"""
        jsonrpc = message.get("jsonrpc", "2.0")
        method = message.get("method")
        params = message.get("params", {})
        msg_id = message.get("id")
        
        try:
            # Handle different methods
            if method == "initialize":
                return await self._handle_initialize(msg_id, params)
            elif method == "tools/list":
                return await self._handle_tools_list(msg_id)
            elif method == "tools/call":
                return await self._handle_tool_call(msg_id, params)
            elif method == "ping":
                return self._create_response(msg_id, {})
            else:
                return self._create_error(msg_id, -32601, f"Method not found: {method}")
                
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            return self._create_error(msg_id, -32603, str(e))
    
    async def _handle_initialize(self, msg_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle initialize request"""
        # Extract client info
        client_info = params.get("clientInfo", {})
        logger.info(f"Client connected: {client_info.get('name', 'Unknown')} v{client_info.get('version', 'Unknown')}")
        
        # Initialize database if needed
        database_url = os.environ.get("DATABASE_URI")
        if database_url and not hasattr(db_connection, '_pool') or not db_connection._pool:
            try:
                await db_connection.pool_connect(database_url)
                logger.info("Database connection established")
            except Exception as e:
                logger.warning(f"Failed to connect to database: {obfuscate_password(str(e))}")
        
        # Return server info and capabilities
        return self._create_response(msg_id, {
            "protocolVersion": PROTOCOL_VERSION,
            "serverInfo": self.server_info,
            "capabilities": self.capabilities
        })
    
    async def _handle_tools_list(self, msg_id: str) -> Dict[str, Any]:
        """Handle tools/list request"""
        tools_list = []
        for name, tool_info in self.tools.items():
            tools_list.append({
                "name": name,
                "description": tool_info["description"],
                "inputSchema": tool_info["inputSchema"]
            })
        
        return self._create_response(msg_id, {"tools": tools_list})
    
    async def _handle_tool_call(self, msg_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tools/call request"""
        tool_name = params.get("name")
        tool_params = params.get("arguments", {})
        
        if tool_name not in self.tools:
            return self._create_error(msg_id, -32602, f"Unknown tool: {tool_name}")
        
        try:
            # Execute the tool
            result = await self._execute_tool(tool_name, tool_params)
            
            # Return result as text content
            return self._create_response(msg_id, {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(result, indent=2) if isinstance(result, (dict, list)) else str(result)
                    }
                ]
            })
        except Exception as e:
            logger.error(f"Tool execution error: {e}")
            return self._create_error(msg_id, -32603, str(e))
    
    async def _execute_tool(self, tool_name: str, params: Dict[str, Any]) -> Any:
        """Execute a specific tool"""
        if tool_name == "test-connection":
            return await self._test_connection(params)
        elif tool_name == "list-schemas":
            return await self._list_schemas()
        elif tool_name == "list-tables":
            return await self._list_tables(params)
        elif tool_name == "execute-query":
            return await self._execute_query(params)
        elif tool_name == "explain-query":
            return await self._explain_query(params)
        elif tool_name == "get-slow-queries":
            return await self._get_slow_queries(params)
        elif tool_name == "health-check":
            return await self._health_check(params)
        elif tool_name == "suggest-indexes":
            return await self._suggest_indexes(params)
        elif tool_name == "get-table-stats":
            return await self._get_table_stats(params)
        elif tool_name == "analyze-index-usage":
            return await self._analyze_index_usage(params)
        elif tool_name == "get-blocking-queries":
            return await self._get_blocking_queries(params)
        else:
            raise ValueError(f"Unknown tool: {tool_name}")
    
    async def _test_connection(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Test database connection"""
        database_url = params.get("database_url") or os.environ.get("DATABASE_URI")
        
        if not database_url:
            return {"success": False, "error": "No database URL provided"}
        
        try:
            # Try to connect if not already connected
            if not db_connection._pool:
                await db_connection.pool_connect(database_url)
            
            # Test with a simple query
            sql_driver = SqlDriver(conn=db_connection)
            await sql_driver.execute_query("SELECT 1")
            
            return {"success": True, "message": "Connection successful"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _list_schemas(self) -> List[Dict[str, Any]]:
        """List all schemas in the database"""
        sql_driver = SqlDriver(conn=db_connection)
        rows = await sql_driver.execute_query("""
            SELECT
                schema_name,
                schema_owner,
                CASE
                    WHEN schema_name LIKE 'pg_%' THEN 'System Schema'
                    WHEN schema_name = 'information_schema' THEN 'System Information Schema'
                    ELSE 'User Schema'
                END as schema_type
            FROM information_schema.schemata
            ORDER BY schema_type, schema_name
        """)
        
        return [row.cells for row in rows] if rows else []
    
    async def _list_tables(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """List tables in a schema"""
        schema = params.get("schema", "public")
        sql_driver = SafeSqlDriver(sql_driver=SqlDriver(conn=db_connection))
        
        rows = await SafeSqlDriver.execute_param_query(
            sql_driver,
            """
            SELECT table_schema, table_name, table_type
            FROM information_schema.tables
            WHERE table_schema = {}
            ORDER BY table_name
            """,
            [schema]
        )
        
        return [row.cells for row in rows] if rows else []
    
    async def _execute_query(self, params: Dict[str, Any]) -> Union[List[Dict[str, Any]], str]:
        """Execute a SQL query"""
        query = params.get("query")
        if not query:
            raise ValueError("Query parameter is required")
        
        sql_driver = SqlDriver(conn=db_connection)
        rows = await sql_driver.execute_query(query)
        
        if rows is None:
            return "Query executed successfully (no results)"
        
        return [row.cells for row in rows]
    
    async def _explain_query(self, params: Dict[str, Any]) -> Union[str, Dict[str, Any]]:
        """Explain query execution plan"""
        query = params.get("query")
        if not query:
            raise ValueError("Query parameter is required")
        
        analyze = params.get("analyze", False)
        buffers = params.get("buffers", False)
        format_type = params.get("format", "text")
        
        sql_driver = SqlDriver(conn=db_connection)
        
        # Build EXPLAIN command
        explain_parts = ["EXPLAIN"]
        options = []
        
        if analyze:
            options.append("ANALYZE TRUE")
        if buffers:
            options.append("BUFFERS TRUE")
        if format_type != "text":
            options.append(f"FORMAT {format_type.upper()}")
        
        if options:
            explain_parts.append(f"({', '.join(options)})")
        
        explain_query = f"{' '.join(explain_parts)} {query}"
        
        try:
            rows = await sql_driver.execute_query(explain_query)
            if format_type == "json" and rows:
                # Parse JSON result
                return json.loads(rows[0].cells["QUERY PLAN"])
            elif rows:
                # Return text format
                return "\n".join(row.cells["QUERY PLAN"] for row in rows)
            else:
                return "No execution plan available"
        except Exception as e:
            return f"Error explaining query: {str(e)}"
    
    async def _get_slow_queries(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get slow queries from pg_stat_statements"""
        limit = params.get("limit", 20)
        min_duration_ms = params.get("min_duration_ms", 1000)
        
        sql_driver = SqlDriver(conn=db_connection)
        
        # Check if pg_stat_statements is available
        check_query = """
            SELECT EXISTS (
                SELECT 1 FROM pg_extension WHERE extname = 'pg_stat_statements'
            )
        """
        
        rows = await sql_driver.execute_query(check_query)
        if not rows or not rows[0].cells["exists"]:
            return [{"error": "pg_stat_statements extension is not installed"}]
        
        # Get slow queries
        query = f"""
            SELECT
                query,
                calls,
                total_exec_time,
                mean_exec_time,
                stddev_exec_time,
                rows,
                100.0 * shared_blks_hit / NULLIF(shared_blks_hit + shared_blks_read, 0) AS hit_percent
            FROM pg_stat_statements
            WHERE mean_exec_time > {min_duration_ms}
            ORDER BY mean_exec_time DESC
            LIMIT {limit}
        """
        
        rows = await sql_driver.execute_query(query)
        return [row.cells for row in rows] if rows else []
    
    async def _health_check(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Perform comprehensive health check"""
        sql_driver = SqlDriver(conn=db_connection)
        health_status = {
            "timestamp": datetime.utcnow().isoformat(),
            "status": "healthy",
            "checks": {}
        }
        
        # Check connection count
        try:
            conn_query = """
                SELECT 
                    count(*) as total_connections,
                    count(*) FILTER (WHERE state = 'active') as active_connections,
                    max_conn.setting::int as max_connections
                FROM pg_stat_activity
                CROSS JOIN pg_settings max_conn
                WHERE max_conn.name = 'max_connections'
                GROUP BY max_conn.setting
            """
            rows = await sql_driver.execute_query(conn_query)
            if rows:
                row = rows[0].cells
                health_status["checks"]["connections"] = {
                    "total": row["total_connections"],
                    "active": row["active_connections"],
                    "max": row["max_connections"],
                    "usage_percent": round(100.0 * row["total_connections"] / row["max_connections"], 2)
                }
        except Exception as e:
            health_status["checks"]["connections"] = {"error": str(e)}
        
        # Check database size
        try:
            size_query = """
                SELECT 
                    pg_database_size(current_database()) as database_size,
                    pg_size_pretty(pg_database_size(current_database())) as database_size_pretty
            """
            rows = await sql_driver.execute_query(size_query)
            if rows:
                row = rows[0].cells
                health_status["checks"]["database_size"] = {
                    "bytes": row["database_size"],
                    "pretty": row["database_size_pretty"]
                }
        except Exception as e:
            health_status["checks"]["database_size"] = {"error": str(e)}
        
        # Check cache hit ratio
        try:
            cache_query = """
                SELECT 
                    sum(heap_blks_read) as heap_read,
                    sum(heap_blks_hit) as heap_hit,
                    sum(heap_blks_hit) / NULLIF(sum(heap_blks_hit) + sum(heap_blks_read), 0) as cache_hit_ratio
                FROM pg_statio_user_tables
            """
            rows = await sql_driver.execute_query(cache_query)
            if rows:
                row = rows[0].cells
                health_status["checks"]["cache"] = {
                    "heap_read": row["heap_read"],
                    "heap_hit": row["heap_hit"],
                    "hit_ratio": round(float(row["cache_hit_ratio"] or 0) * 100, 2)
                }
        except Exception as e:
            health_status["checks"]["cache"] = {"error": str(e)}
        
        # Determine overall health
        if any("error" in check for check in health_status["checks"].values()):
            health_status["status"] = "degraded"
        
        return health_status
    
    async def _suggest_indexes(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Suggest indexes based on query patterns"""
        limit = params.get("limit", 10)
        min_calls = params.get("min_calls", 10)
        min_duration_ms = params.get("min_duration_ms", 100)
        
        sql_driver = SqlDriver(conn=db_connection)
        
        # Get frequently executed queries without good indexes
        query = f"""
            WITH query_stats AS (
                SELECT 
                    query,
                    calls,
                    mean_exec_time,
                    total_exec_time
                FROM pg_stat_statements
                WHERE calls >= {min_calls}
                    AND mean_exec_time >= {min_duration_ms}
                    AND query NOT LIKE '%pg_stat_statements%'
                ORDER BY total_exec_time DESC
                LIMIT {limit}
            )
            SELECT * FROM query_stats
        """
        
        rows = await sql_driver.execute_query(query)
        suggestions = []
        
        for row in rows or []:
            query_text = row.cells["query"]
            
            # Simple pattern matching for index suggestions
            suggestion = {
                "query": query_text,
                "calls": row.cells["calls"],
                "mean_exec_time_ms": row.cells["mean_exec_time"],
                "suggestions": []
            }
            
            # Look for WHERE clauses
            if "WHERE" in query_text.upper():
                suggestion["suggestions"].append("Consider adding indexes on columns used in WHERE clauses")
            
            # Look for JOINs
            if "JOIN" in query_text.upper():
                suggestion["suggestions"].append("Consider adding indexes on join columns")
            
            # Look for ORDER BY
            if "ORDER BY" in query_text.upper():
                suggestion["suggestions"].append("Consider adding indexes on ORDER BY columns")
            
            suggestions.append(suggestion)
        
        return suggestions
    
    async def _get_table_stats(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get table statistics"""
        schema = params.get("schema", "public")
        table_pattern = params.get("table_pattern", "%")
        include_indexes = params.get("include_indexes", True)
        
        sql_driver = SafeSqlDriver(sql_driver=SqlDriver(conn=db_connection))
        
        # Get table stats
        query = """
            SELECT 
                schemaname,
                tablename,
                pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as total_size,
                pg_size_pretty(pg_table_size(schemaname||'.'||tablename)) as table_size,
                pg_size_pretty(pg_indexes_size(schemaname||'.'||tablename)) as indexes_size,
                n_live_tup as row_count,
                n_dead_tup as dead_rows,
                last_vacuum,
                last_autovacuum,
                last_analyze,
                last_autoanalyze
            FROM pg_stat_user_tables
            WHERE schemaname = {}
                AND tablename LIKE {}
            ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
        """
        
        rows = await SafeSqlDriver.execute_param_query(
            sql_driver, query, [schema, table_pattern]
        )
        
        return [row.cells for row in rows] if rows else []
    
    async def _analyze_index_usage(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze index usage"""
        schema = params.get("schema", "public")
        min_size_mb = params.get("min_size_mb", 1)
        
        sql_driver = SafeSqlDriver(sql_driver=SqlDriver(conn=db_connection))
        
        # Find unused or poorly used indexes
        query = """
            SELECT 
                schemaname,
                tablename,
                indexname,
                pg_size_pretty(pg_relation_size(indexrelid)) as index_size,
                idx_scan as index_scans,
                idx_tup_read as tuples_read,
                idx_tup_fetch as tuples_fetched,
                CASE 
                    WHEN idx_scan = 0 THEN 'UNUSED'
                    WHEN idx_scan < 100 THEN 'RARELY_USED'
                    ELSE 'ACTIVE'
                END as usage_status
            FROM pg_stat_user_indexes
            WHERE schemaname = {}
                AND pg_relation_size(indexrelid) > {} * 1024 * 1024
            ORDER BY idx_scan, pg_relation_size(indexrelid) DESC
        """
        
        rows = await SafeSqlDriver.execute_param_query(
            sql_driver, query, [schema, min_size_mb]
        )
        
        return [row.cells for row in rows] if rows else []
    
    async def _get_blocking_queries(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get blocking queries"""
        min_duration_ms = params.get("min_duration_ms", 1000)
        
        sql_driver = SqlDriver(conn=db_connection)
        
        # Find blocking queries
        query = f"""
            SELECT 
                blocked_locks.pid AS blocked_pid,
                blocked_activity.usename AS blocked_user,
                blocking_locks.pid AS blocking_pid,
                blocking_activity.usename AS blocking_user,
                blocked_activity.query AS blocked_query,
                blocking_activity.query AS blocking_query,
                blocked_activity.state AS blocked_state,
                blocking_activity.state AS blocking_state,
                now() - blocked_activity.query_start AS blocked_duration,
                now() - blocking_activity.query_start AS blocking_duration
            FROM pg_catalog.pg_locks blocked_locks
            JOIN pg_catalog.pg_stat_activity blocked_activity ON blocked_activity.pid = blocked_locks.pid
            JOIN pg_catalog.pg_locks blocking_locks 
                ON blocking_locks.locktype = blocked_locks.locktype
                AND blocking_locks.DATABASE IS NOT DISTINCT FROM blocked_locks.DATABASE
                AND blocking_locks.relation IS NOT DISTINCT FROM blocked_locks.relation
                AND blocking_locks.page IS NOT DISTINCT FROM blocked_locks.page
                AND blocking_locks.tuple IS NOT DISTINCT FROM blocked_locks.tuple
                AND blocking_locks.virtualxid IS NOT DISTINCT FROM blocked_locks.virtualxid
                AND blocking_locks.transactionid IS NOT DISTINCT FROM blocked_locks.transactionid
                AND blocking_locks.classid IS NOT DISTINCT FROM blocked_locks.classid
                AND blocking_locks.objid IS NOT DISTINCT FROM blocked_locks.objid
                AND blocking_locks.objsubid IS NOT DISTINCT FROM blocked_locks.objsubid
                AND blocking_locks.pid != blocked_locks.pid
            JOIN pg_catalog.pg_stat_activity blocking_activity ON blocking_activity.pid = blocking_locks.pid
            WHERE NOT blocked_locks.GRANTED
                AND (now() - blocked_activity.query_start) > interval '{min_duration_ms} milliseconds'
        """
        
        rows = await sql_driver.execute_query(query)
        return [row.cells for row in rows] if rows else []
    
    def _create_response(self, msg_id: Optional[str], result: Any) -> Dict[str, Any]:
        """Create a JSON-RPC response"""
        response = {
            "jsonrpc": "2.0",
            "result": result
        }
        if msg_id is not None:
            response["id"] = msg_id
        return response
    
    def _create_error(self, msg_id: Optional[str], code: int, message: str) -> Dict[str, Any]:
        """Create a JSON-RPC error response"""
        response = {
            "jsonrpc": "2.0",
            "error": {
                "code": code,
                "message": message
            }
        }
        if msg_id is not None:
            response["id"] = msg_id
        return response


# Create global MCP server instance
mcp_server = MCPServer()


async def handle_sse(request: web.Request) -> web.StreamResponse:
    """Handle SSE connections for server->client communication"""
    client_id = str(uuid.uuid4())
    
    async with sse_response(request) as resp:
        # Store connection
        active_connections[client_id] = resp
        logger.info(f"SSE client connected: {client_id}")
        
        try:
            # Send initial connection event
            await resp.send(json.dumps({
                "jsonrpc": "2.0",
                "method": "connection/ready",
                "params": {}
            }), event="message")
            
            # Keep connection alive
            while not resp.task.done():
                await asyncio.sleep(30)  # Send ping every 30 seconds
                await resp.send(json.dumps({
                    "jsonrpc": "2.0",
                    "method": "ping",
                    "params": {}
                }), event="message")
                
        except Exception as e:
            logger.error(f"SSE error: {e}")
        finally:
            # Remove connection
            active_connections.pop(client_id, None)
            logger.info(f"SSE client disconnected: {client_id}")
    
    return resp


async def handle_message(request: web.Request) -> web.Response:
    """Handle client->server messages via POST"""
    try:
        # Parse JSON-RPC message
        data = await request.json()
        logger.debug(f"Received message: {data}")
        
        # Process message
        response = await mcp_server.handle_message(data)
        
        # Send response to all SSE clients
        response_text = json.dumps(response)
        for client_id, client_resp in list(active_connections.items()):
            try:
                await client_resp.send(response_text, event="message")
            except Exception as e:
                logger.error(f"Failed to send to client {client_id}: {e}")
                active_connections.pop(client_id, None)
        
        # Return response directly
        return web.json_response(response)
        
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON: {e}")
        return web.json_response({
            "jsonrpc": "2.0",
            "error": {
                "code": -32700,
                "message": "Parse error"
            }
        }, status=400)
    except Exception as e:
        logger.error(f"Message handling error: {e}")
        return web.json_response({
            "jsonrpc": "2.0",
            "error": {
                "code": -32603,
                "message": str(e)
            }
        }, status=500)


async def health_check(request: web.Request) -> web.Response:
    """Health check endpoint"""
    health_info = {
        "status": "healthy",
        "server": "postgres-mcp",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "database_connected": hasattr(db_connection, '_pool') and db_connection._pool is not None
    }
    
    # Check if database is connected
    if hasattr(db_connection, '_pool') and db_connection._pool:
        try:
            async with db_connection._pool.connection() as conn:
                async with conn.cursor() as cur:
                    await cur.execute("SELECT 1")
                    health_info["database_status"] = "connected"
        except Exception as e:
            health_info["database_status"] = f"error: {str(e)}"
            health_info["status"] = "degraded"
    else:
        health_info["database_status"] = "not connected"
        health_info["status"] = "degraded"
    
    return web.json_response(health_info)


def create_app() -> web.Application:
    """Create the web application"""
    app = web.Application()
    
    # Add routes
    app.router.add_get("/sse", handle_sse)
    app.router.add_post("/message", handle_message)
    app.router.add_get("/health", health_check)
    
    # Add CORS middleware
    @web.middleware
    async def cors_middleware(request: web.Request, handler):
        response = await handler(request)
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response
    
    app.middlewares.append(cors_middleware)
    
    return app


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="PostgreSQL MCP Server with SSE")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    args = parser.parse_args()
    
    # Initialize database connection from environment
    database_url = os.environ.get("DATABASE_URI")
    if database_url:
        try:
            await db_connection.pool_connect(database_url)
            logger.info("Database connection initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize database: {obfuscate_password(str(e))}")
    else:
        logger.warning("No DATABASE_URI environment variable set")
    
    # Create and run the app
    app = create_app()
    runner = web.AppRunner(app)
    await runner.setup()
    
    site = web.TCPSite(runner, args.host, args.port)
    await site.start()
    
    logger.info(f"PostgreSQL MCP SSE Server running on http://{args.host}:{args.port}")
    logger.info("Endpoints:")
    logger.info(f"  - SSE: http://{args.host}:{args.port}/sse")
    logger.info(f"  - Messages: http://{args.host}:{args.port}/message")
    logger.info(f"  - Health: http://{args.host}:{args.port}/health")
    
    # Keep running until interrupted
    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        pass
    finally:
        await runner.cleanup()
        await db_connection.close()


if __name__ == "__main__":
    asyncio.run(main())