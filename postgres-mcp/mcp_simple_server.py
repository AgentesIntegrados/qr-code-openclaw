#!/usr/bin/env python3
"""PostgreSQL MCP Server - Simple HTTP Implementation for n8n"""
import asyncio
import json
import os
import sys
from typing import Any, Dict, List
from aiohttp import web
import aiohttp_cors
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from handlers import PostgresHandlers

class SimpleMCPServer:
    """Simple MCP Server for n8n integration"""
    
    def __init__(self, host="0.0.0.0", port=8082):
        self.host = host
        self.port = port
        self.app = web.Application()
        self.bearer_token = os.environ.get('POSTGRES_MCP_TOKEN', 'EYjpWqb7YS1kJ0TKdJtVRN7Zj654NZbq6Ewe7RCHtPs')
        self.setup_routes()
        self.setup_cors()
        
        # Define tools
        self.tools = [
            {
                "name": "postgres.test_connection",
                "description": "Test PostgreSQL database connection",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "database_url": {
                            "type": "string",
                            "description": "PostgreSQL connection string"
                        }
                    }
                }
            },
            {
                "name": "postgres.list_schemas",
                "description": "List all schemas in the database",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "postgres.list_tables",
                "description": "List all tables in a schema",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "schema": {
                            "type": "string",
                            "description": "Schema name",
                            "default": "public"
                        }
                    }
                }
            },
            {
                "name": "postgres.execute_query",
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
            },
            {
                "name": "postgres.health_check",
                "description": "Check database health",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            }
        ]
    
    def setup_cors(self):
        """Configure CORS"""
        cors = aiohttp_cors.setup(self.app, defaults={
            "*": aiohttp_cors.ResourceOptions(
                allow_credentials=True,
                expose_headers="*",
                allow_headers="*",
                allow_methods="*"
            )
        })
        
        for route in list(self.app.router.routes()):
            cors.add(route)
    
    def setup_routes(self):
        """Setup HTTP routes"""
        self.app.router.add_post('/mcp', self.handle_mcp_request)
        self.app.router.add_get('/health', self.health_check)
        self.app.router.add_get('/', self.info)
    
    async def info(self, request):
        """Info page"""
        return web.json_response({
            "name": "PostgreSQL MCP Server",
            "version": "0.1.0",
            "protocol": "MCP",
            "transport": ["http"],
            "endpoint": f"http://{self.host}:{self.port}/mcp",
            "tools": [tool["name"] for tool in self.tools]
        })
    
    async def health_check(self, request):
        """Health check endpoint"""
        return web.json_response({"status": "ok", "timestamp": datetime.now().isoformat()})
    
    async def handle_mcp_request(self, request):
        """Handle MCP JSON-RPC requests"""
        try:
            # Check Bearer token
            auth_header = request.headers.get('Authorization', '')
            if auth_header:
                if not auth_header.startswith('Bearer '):
                    return web.json_response({
                        "jsonrpc": "2.0",
                        "error": {
                            "code": -32600,
                            "message": "Invalid Authorization header"
                        },
                        "id": None
                    }, status=401)
                
                token = auth_header[7:]
                if token != self.bearer_token:
                    return web.json_response({
                        "jsonrpc": "2.0",
                        "error": {
                            "code": -32600,
                            "message": "Invalid token"
                        },
                        "id": None
                    }, status=401)
            
            data = await request.json()
            
            # Basic JSON-RPC 2.0 structure
            if "jsonrpc" not in data or data["jsonrpc"] != "2.0":
                return web.json_response({
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32600,
                        "message": "Invalid Request"
                    },
                    "id": data.get("id")
                })
            
            method = data.get("method")
            params = data.get("params", {})
            request_id = data.get("id")
            
            # Handle different MCP methods
            if method == "initialize":
                result = {
                    "protocolVersion": "0.1.0",
                    "capabilities": {
                        "tools": {},
                        "resources": {},
                        "prompts": {},
                        "logging": {}
                    },
                    "serverInfo": {
                        "name": "postgres-mcp-simple",
                        "version": "0.1.0"
                    }
                }
            
            elif method == "tools/list":
                result = {"tools": self.tools}
            
            elif method == "tools/call":
                tool_name = params.get("name")
                tool_args = params.get("arguments", {})
                
                # Call the appropriate handler
                result = await self.call_tool(tool_name, tool_args)
            
            else:
                return web.json_response({
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    },
                    "id": request_id
                })
            
            # Return successful response
            return web.json_response({
                "jsonrpc": "2.0",
                "result": result,
                "id": request_id
            })
            
        except Exception as e:
            return web.json_response({
                "jsonrpc": "2.0",
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                },
                "id": data.get("id") if "data" in locals() else None
            })
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool and return result"""
        try:
            # Remove 'postgres.' prefix if present
            tool_name = name.replace('postgres.', '')
            
            # Call the appropriate handler
            if tool_name == "test_connection":
                content = await PostgresHandlers.handle_test_connection(arguments)
            elif tool_name == "list_schemas":
                content = await PostgresHandlers.handle_list_schemas(arguments)
            elif tool_name == "list_tables":
                content = await PostgresHandlers.handle_list_tables(arguments)
            elif tool_name == "execute_query":
                content = await PostgresHandlers.handle_execute_query(arguments)
            elif tool_name == "health_check":
                content = await PostgresHandlers.handle_health_check(arguments)
            else:
                raise ValueError(f"Unknown tool: {name}")
            
            # Format response
            return {
                "content": [
                    {"type": "text", "text": c.text}
                    for c in content
                ]
            }
            
        except Exception as e:
            return {
                "content": [
                    {"type": "text", "text": f"Error: {str(e)}"}
                ]
            }
    
    async def start(self):
        """Start the server"""
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, self.host, self.port)
        
        print(f"🚀 PostgreSQL MCP Simple Server")
        print(f"📍 Local: http://{self.host}:{self.port}")
        print(f"🌐 External: https://postgres-server.agentesintegrados.com")
        print(f"🔌 MCP Endpoint: https://postgres-server.agentesintegrados.com/mcp")
        print(f"🔐 Bearer Token: {self.bearer_token}")
        print(f"🛠️  For n8n MCP Client:")
        print(f"   - Server URL: https://postgres-server.agentesintegrados.com/mcp")
        print(f"   - Transport: HTTP")
        print(f"   - Auth: Bearer Token (optional)")
        print(f"📊 Database: {os.environ.get('DATABASE_URI', 'Not configured')}")
        print(f"\n📝 Example MCP Request:")
        print(f'curl -X POST https://postgres-server.agentesintegrados.com/mcp \\')
        print(f'  -H "Content-Type: application/json" \\')
        print(f'  -H "Authorization: Bearer {self.bearer_token}" \\')
        print(f'  -d \'{{"jsonrpc":"2.0","method":"tools/list","params":{{}},"id":1}}\'')
        
        await site.start()
        
        # Keep the server running
        await asyncio.Event().wait()

async def main():
    """Main entry point"""
    server = SimpleMCPServer(host="0.0.0.0", port=8082)
    await server.start()

if __name__ == "__main__":
    asyncio.run(main())