#!/usr/bin/env python3
"""PostgreSQL SSE Server - Servidor híbrido com endpoints HTTP/SSE"""
import asyncio
import json
import os
import sys
import secrets
from aiohttp import web
from aiohttp_sse import sse_response
import aiohttp_cors
from datetime import datetime
import psycopg
from typing import Dict, Any, List
from functools import wraps

# Add parent directory to path to import handlers
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from handlers import PostgresHandlers

# Autenticação Bearer
BEARER_TOKEN = os.environ.get('POSTGRES_SSE_TOKEN') or secrets.token_urlsafe(32)

def require_auth(func):
    """Decorator para exigir autenticação Bearer"""
    @wraps(func)
    async def wrapper(self, request):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return web.json_response(
                {'error': 'Missing or invalid Authorization header'},
                status=401,
                headers={'WWW-Authenticate': 'Bearer'}
            )
        
        token = auth_header[7:]  # Remove 'Bearer ' prefix
        if token != BEARER_TOKEN:
            return web.json_response(
                {'error': 'Invalid token'},
                status=401
            )
        
        return await func(self, request)
    return wrapper

class PostgresSSEServer:
    def __init__(self, port=8081):
        self.port = port
        self.app = web.Application()
        self.setup_routes()
        self.setup_cors()
        
        # Exibir token no início
        print(f"🔐 Bearer Token: {BEARER_TOKEN}")
        print(f"💡 Configure POSTGRES_SSE_TOKEN como variável de ambiente para usar um token fixo")
        
    def setup_cors(self):
        """Configurar CORS para permitir acesso do navegador"""
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
        """Configurar rotas HTTP e SSE"""
        # Rotas SSE
        self.app.router.add_get('/sse/test-connection', self.sse_test_connection)
        self.app.router.add_get('/sse/health-check', self.sse_health_check)
        self.app.router.add_get('/sse/monitor-queries', self.sse_monitor_queries)
        self.app.router.add_get('/sse/monitor-locks', self.sse_monitor_locks)
        
        # Rotas HTTP regulares
        self.app.router.add_post('/api/test-connection', self.api_test_connection)
        self.app.router.add_get('/api/list-schemas', self.api_list_schemas)
        self.app.router.add_get('/api/list-tables', self.api_list_tables)
        self.app.router.add_post('/api/execute-query', self.api_execute_query)
        self.app.router.add_post('/api/explain-query', self.api_explain_query)
        self.app.router.add_get('/api/slow-queries', self.api_slow_queries)
        self.app.router.add_get('/api/health-check', self.api_health_check)
        self.app.router.add_get('/api/suggest-indexes', self.api_suggest_indexes)
        self.app.router.add_get('/api/table-stats', self.api_table_stats)
        self.app.router.add_get('/api/index-usage', self.api_index_usage)
        self.app.router.add_get('/api/blocking-queries', self.api_blocking_queries)
        
        # Página de status
        self.app.router.add_get('/', self.index)
        
    async def index(self, request):
        """Página inicial com status e documentação"""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>PostgreSQL MCP - SSE Server</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .endpoint { background: #f0f0f0; padding: 10px; margin: 10px 0; border-radius: 5px; }
                .sse { background: #e8f5e9; }
                .api { background: #e3f2fd; }
                code { background: #ddd; padding: 2px 5px; border-radius: 3px; }
            </style>
        </head>
        <body>
            <h1>PostgreSQL MCP - SSE Server</h1>
            <p>Servidor híbrido com endpoints HTTP e Server-Sent Events</p>
            
            <h2>SSE Endpoints (Real-time)</h2>
            <div class="endpoint sse">
                <strong>GET /sse/test-connection</strong> - Testa conexão continuamente
            </div>
            <div class="endpoint sse">
                <strong>GET /sse/health-check</strong> - Monitora saúde do banco em tempo real
            </div>
            <div class="endpoint sse">
                <strong>GET /sse/monitor-queries</strong> - Monitora queries em execução
            </div>
            <div class="endpoint sse">
                <strong>GET /sse/monitor-locks</strong> - Monitora bloqueios em tempo real
            </div>
            
            <h2>API Endpoints (HTTP)</h2>
            <div class="endpoint api">
                <strong>POST /api/test-connection</strong> - Testa conexão
            </div>
            <div class="endpoint api">
                <strong>GET /api/list-schemas</strong> - Lista schemas
            </div>
            <div class="endpoint api">
                <strong>GET /api/list-tables?schema=public</strong> - Lista tabelas
            </div>
            <div class="endpoint api">
                <strong>POST /api/execute-query</strong> - Executa query
            </div>
            <div class="endpoint api">
                <strong>POST /api/explain-query</strong> - Analisa plano de execução
            </div>
            <div class="endpoint api">
                <strong>GET /api/slow-queries</strong> - Queries lentas
            </div>
            <div class="endpoint api">
                <strong>GET /api/health-check</strong> - Verificação de saúde
            </div>
            <div class="endpoint api">
                <strong>GET /api/suggest-indexes</strong> - Sugestões de índices
            </div>
            <div class="endpoint api">
                <strong>GET /api/table-stats</strong> - Estatísticas de tabelas
            </div>
            <div class="endpoint api">
                <strong>GET /api/index-usage</strong> - Análise de uso de índices
            </div>
            <div class="endpoint api">
                <strong>GET /api/blocking-queries</strong> - Queries bloqueadas
            </div>
            
            <h3>Autenticação:</h3>
            <p>Todos os endpoints requerem autenticação Bearer Token no header:</p>
            <pre><code>Authorization: Bearer YOUR_TOKEN</code></pre>
            
            <h3>Exemplo SSE com JavaScript:</h3>
            <pre><code>const eventSource = new EventSource('http://localhost:8080/sse/health-check', {
    headers: {
        'Authorization': 'Bearer YOUR_TOKEN'
    }
});
eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('Health update:', data);
};</code></pre>
            
            <h3>Exemplo API com cURL:</h3>
            <pre><code>curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8080/api/list-schemas</code></pre>
        </body>
        </html>
        """
        return web.Response(text=html, content_type='text/html')
    
    # SSE Endpoints
    @require_auth
    async def sse_test_connection(self, request):
        """SSE endpoint para testar conexão continuamente"""
        async with sse_response(request) as resp:
            while True:
                try:
                    result = await PostgresHandlers.handle_test_connection({})
                    await resp.send(json.dumps({
                        'timestamp': datetime.now().isoformat(),
                        'status': 'connected' if 'successfully' in result[0].text else 'failed',
                        'message': result[0].text
                    }))
                except Exception as e:
                    await resp.send(json.dumps({
                        'timestamp': datetime.now().isoformat(),
                        'status': 'error',
                        'error': str(e)
                    }))
                await asyncio.sleep(5)  # Check every 5 seconds
        return resp
    
    @require_auth
    async def sse_health_check(self, request):
        """SSE endpoint para monitorar saúde do banco"""
        async with sse_response(request) as resp:
            while True:
                try:
                    result = await PostgresHandlers.handle_health_check({})
                    health_data = result[0].text
                    await resp.send(json.dumps({
                        'timestamp': datetime.now().isoformat(),
                        'health_report': health_data
                    }))
                except Exception as e:
                    await resp.send(json.dumps({
                        'timestamp': datetime.now().isoformat(),
                        'error': str(e)
                    }))
                await asyncio.sleep(10)  # Check every 10 seconds
        return resp
    
    @require_auth
    async def sse_monitor_queries(self, request):
        """SSE endpoint para monitorar queries em execução"""
        async with sse_response(request) as resp:
            while True:
                try:
                    # Get active queries
                    query = """
                    SELECT 
                        pid,
                        usename,
                        application_name,
                        client_addr,
                        state,
                        query,
                        EXTRACT(EPOCH FROM (now() - query_start))::int as duration_seconds
                    FROM pg_stat_activity
                    WHERE state != 'idle'
                    AND pid != pg_backend_pid()
                    ORDER BY query_start;
                    """
                    result = await PostgresHandlers.handle_execute_query({'query': query})
                    await resp.send(json.dumps({
                        'timestamp': datetime.now().isoformat(),
                        'active_queries': result[0].text
                    }))
                except Exception as e:
                    await resp.send(json.dumps({
                        'timestamp': datetime.now().isoformat(),
                        'error': str(e)
                    }))
                await asyncio.sleep(2)  # Check every 2 seconds
        return resp
    
    @require_auth
    async def sse_monitor_locks(self, request):
        """SSE endpoint para monitorar bloqueios"""
        async with sse_response(request) as resp:
            while True:
                try:
                    result = await PostgresHandlers.handle_get_blocking_queries({})
                    await resp.send(json.dumps({
                        'timestamp': datetime.now().isoformat(),
                        'blocking_info': result[0].text
                    }))
                except Exception as e:
                    await resp.send(json.dumps({
                        'timestamp': datetime.now().isoformat(),
                        'error': str(e)
                    }))
                await asyncio.sleep(3)  # Check every 3 seconds
        return resp
    
    # HTTP API Endpoints
    @require_auth
    async def api_test_connection(self, request):
        """API endpoint para testar conexão"""
        data = await request.json() if request.body_exists else {}
        result = await PostgresHandlers.handle_test_connection(data)
        return web.json_response({'result': result[0].text})
    
    @require_auth
    async def api_list_schemas(self, request):
        """API endpoint para listar schemas"""
        result = await PostgresHandlers.handle_list_schemas({})
        return web.json_response({'schemas': result[0].text})
    
    @require_auth
    async def api_list_tables(self, request):
        """API endpoint para listar tabelas"""
        schema = request.query.get('schema', 'public')
        result = await PostgresHandlers.handle_list_tables({'schema': schema})
        return web.json_response({'tables': result[0].text})
    
    @require_auth
    async def api_execute_query(self, request):
        """API endpoint para executar query"""
        data = await request.json()
        result = await PostgresHandlers.handle_execute_query(data)
        return web.json_response({'result': result[0].text})
    
    @require_auth
    async def api_explain_query(self, request):
        """API endpoint para explain query"""
        data = await request.json()
        result = await PostgresHandlers.handle_explain_query(data)
        return web.json_response({'plan': result[0].text})
    
    @require_auth
    async def api_slow_queries(self, request):
        """API endpoint para queries lentas"""
        min_duration = int(request.query.get('min_duration_ms', 1000))
        limit = int(request.query.get('limit', 20))
        result = await PostgresHandlers.handle_get_slow_queries({
            'min_duration_ms': min_duration,
            'limit': limit
        })
        return web.json_response({'slow_queries': result[0].text})
    
    @require_auth
    async def api_health_check(self, request):
        """API endpoint para health check"""
        result = await PostgresHandlers.handle_health_check({})
        return web.json_response({'health': result[0].text})
    
    @require_auth
    async def api_suggest_indexes(self, request):
        """API endpoint para sugestões de índices"""
        result = await PostgresHandlers.handle_suggest_indexes({})
        return web.json_response({'suggestions': result[0].text})
    
    @require_auth
    async def api_table_stats(self, request):
        """API endpoint para estatísticas de tabelas"""
        schema = request.query.get('schema', 'public')
        result = await PostgresHandlers.handle_get_table_stats({'schema': schema})
        return web.json_response({'stats': result[0].text})
    
    @require_auth
    async def api_index_usage(self, request):
        """API endpoint para análise de uso de índices"""
        schema = request.query.get('schema', 'public')
        result = await PostgresHandlers.handle_analyze_index_usage({'schema': schema})
        return web.json_response({'index_analysis': result[0].text})
    
    @require_auth
    async def api_blocking_queries(self, request):
        """API endpoint para queries bloqueadas"""
        result = await PostgresHandlers.handle_get_blocking_queries({})
        return web.json_response({'blocking_queries': result[0].text})
    
    def run(self):
        """Iniciar servidor SSE"""
        print(f"PostgreSQL SSE Server running on http://localhost:{self.port}")
        print(f"MCP Server continua disponível via stdio")
        print("\nEndpoints disponíveis:")
        print("- SSE: /sse/test-connection, /sse/health-check, /sse/monitor-queries, /sse/monitor-locks")
        print("- API: /api/* endpoints")
        web.run_app(self.app, host='0.0.0.0', port=self.port)

if __name__ == "__main__":
    server = PostgresSSEServer()
    server.run()