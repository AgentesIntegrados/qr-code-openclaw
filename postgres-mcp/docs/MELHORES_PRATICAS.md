# 🌟 Melhores Práticas - PostgreSQL MCP v2.0

## 🎯 Filosofia do Projeto

> "Simples, mas poderoso. Seguro por padrão. Útil desde o primeiro uso."

## 📋 Práticas de Desenvolvimento

### 1. Código Limpo

```python
# ❌ Evite
def h(q):
    r = psycopg.connect(db).cursor().execute(q).fetchall()
    return r

# ✅ Prefira
async def execute_query_safely(query: str) -> List[Dict[str, Any]]:
    """
    Execute a read-only query with proper error handling.
    
    Args:
        query: SQL query to execute (SELECT only)
        
    Returns:
        List of results as dictionaries
        
    Raises:
        ValueError: If query is not SELECT
        DatabaseError: If query execution fails
    """
    if not query.strip().upper().startswith('SELECT'):
        raise ValueError("Only SELECT queries are allowed")
        
    try:
        async with get_connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(query)
                return await cur.fetchall()
    except Exception as e:
        logger.error(f"Query execution failed: {e}")
        raise
```

### 2. Tratamento de Erros

```python
# Hierarquia de erros clara
class MCPError(Exception):
    """Base exception for MCP errors"""

class ConnectionError(MCPError):
    """Database connection errors"""

class QueryError(MCPError):
    """Query execution errors"""

class ValidationError(MCPError):
    """Input validation errors"""

# Uso consistente
try:
    result = await execute_query(query)
except ConnectionError:
    return error_response("Database connection failed")
except QueryError as e:
    return error_response(f"Query error: {str(e)}")
except Exception as e:
    logger.exception("Unexpected error")
    return error_response("Internal error occurred")
```

### 3. Validação de Entrada

```python
# Sempre valide e sanitize
def validate_schema_name(schema: str) -> str:
    """Validate and sanitize schema name."""
    if not schema:
        return "public"
    
    # Apenas letras, números e underscore
    if not re.match(r'^[a-zA-Z0-9_]+$', schema):
        raise ValidationError("Invalid schema name")
    
    # Limite de tamanho
    if len(schema) > 63:  # PostgreSQL limit
        raise ValidationError("Schema name too long")
    
    return schema.lower()
```

## 🔒 Práticas de Segurança

### 1. Princípio do Menor Privilégio

```sql
-- Nunca use superuser para MCP
-- Crie um role específico
CREATE ROLE mcp_reader WITH LOGIN PASSWORD 'secure_pass';

-- Apenas permissões necessárias
GRANT CONNECT ON DATABASE yourdb TO mcp_reader;
GRANT USAGE ON SCHEMA public TO mcp_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO mcp_reader;

-- Para funcionalidades específicas
GRANT pg_read_all_stats TO mcp_reader;  -- Para pg_stat_statements
```

### 2. Prevenção de SQL Injection

```python
# ❌ NUNCA faça isso
query = f"SELECT * FROM {table} WHERE id = {user_input}"

# ✅ Use parametrização
query = "SELECT * FROM %s WHERE id = %s"
cur.execute(query, (AsIs(table), user_input))

# ✅ Ou melhor, use whitelist
ALLOWED_TABLES = ['users', 'messages', 'logs']
if table not in ALLOWED_TABLES:
    raise ValidationError("Invalid table name")
```

### 3. Gerenciamento de Credenciais

```bash
# ❌ Evite
DATABASE_URI="postgresql://user:password@host:5432/db"

# ✅ Use variáveis de ambiente
export DATABASE_URI="${DB_PROTOCOL}://${DB_USER}:${DB_PASS}@${DB_HOST}:${DB_PORT}/${DB_NAME}"

# ✅ Ou use secrets management
DATABASE_URI=$(aws secretsmanager get-secret-value --secret-id prod/db/uri --query SecretString --output text)
```

## 🚀 Práticas de Performance

### 1. Connection Pooling

```python
# Configure pool adequadamente
from contextlib import asynccontextmanager

class DatabasePool:
    def __init__(self, dsn: str, min_size: int = 2, max_size: int = 10):
        self.dsn = dsn
        self.min_size = min_size
        self.max_size = max_size
        self._pool = None
    
    async def init(self):
        self._pool = await asyncpg.create_pool(
            self.dsn,
            min_size=self.min_size,
            max_size=self.max_size,
            command_timeout=60
        )
    
    @asynccontextmanager
    async def acquire(self):
        async with self._pool.acquire() as conn:
            yield conn

# Uso global
db_pool = DatabasePool(DATABASE_URI)
```

### 2. Query Optimization

```python
# Cache de queries repetitivas
from functools import lru_cache
from datetime import datetime, timedelta

@lru_cache(maxsize=100)
def get_cached_table_list(schema: str) -> List[str]:
    """Cache table list for 5 minutes."""
    return fetch_tables(schema)

# Limpar cache periodicamente
def clear_old_cache():
    get_cached_table_list.cache_clear()
```

### 3. Batch Operations

```python
# ❌ Evite múltiplas queries
for table in tables:
    size = get_table_size(table)
    
# ✅ Use uma query
sizes = get_all_table_sizes(tables)
```

## 📊 Práticas de Monitoramento

### 1. Logging Estruturado

```python
import structlog

logger = structlog.get_logger()

# Configure once
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

# Use everywhere
logger.info("query_executed", 
    tool="explain-query",
    duration_ms=23.5,
    query_length=156
)
```

### 2. Métricas Importantes

```python
# Rastreie estas métricas
METRICS = {
    'query_count': Counter('mcp_queries_total', 'Total queries', ['tool']),
    'query_duration': Histogram('mcp_query_seconds', 'Query duration', ['tool']),
    'error_count': Counter('mcp_errors_total', 'Total errors', ['type']),
    'active_connections': Gauge('mcp_connections_active', 'Active connections'),
}

# Use decorador para automatizar
def track_metrics(tool_name: str):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            METRICS['query_count'].labels(tool=tool_name).inc()
            
            with METRICS['query_duration'].labels(tool=tool_name).time():
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    METRICS['error_count'].labels(type=type(e).__name__).inc()
                    raise
        return wrapper
    return decorator
```

### 3. Alertas Inteligentes

```yaml
# Prometheus alerts
groups:
  - name: postgres-mcp
    rules:
      - alert: HighErrorRate
        expr: rate(mcp_errors_total[5m]) > 0.1
        for: 5m
        annotations:
          summary: "High error rate detected"
          
      - alert: SlowQueries
        expr: histogram_quantile(0.95, mcp_query_seconds) > 5
        for: 10m
        annotations:
          summary: "95% of queries taking > 5 seconds"
```

## 🧪 Práticas de Teste

### 1. Testes Unitários

```python
import pytest
from unittest.mock import Mock, patch

@pytest.mark.asyncio
async def test_explain_query_basic():
    """Test basic EXPLAIN functionality."""
    mock_conn = Mock()
    mock_cursor = Mock()
    mock_cursor.fetchall.return_value = [
        ("Seq Scan on users  (cost=0.00..10.00 rows=100)",)
    ]
    
    with patch('psycopg.connect', return_value=mock_conn):
        result = await handle_explain_query({"query": "SELECT * FROM users"})
        
    assert "Seq Scan" in result[0].text
    assert "Sequential scan detected" in result[0].text
```

### 2. Testes de Integração

```python
@pytest.mark.integration
async def test_health_check_real_db():
    """Test health check with real database."""
    # Use test database
    os.environ['DATABASE_URI'] = TEST_DATABASE_URI
    
    result = await handle_health_check({})
    
    assert "Health Score:" in result[0].text
    assert "Connection Statistics:" in result[0].text
```

### 3. Testes de Performance

```python
@pytest.mark.benchmark
def test_query_performance(benchmark):
    """Ensure queries perform within limits."""
    result = benchmark(
        execute_query,
        "SELECT * FROM small_table"
    )
    
    # Query should complete in < 100ms
    assert benchmark.stats['mean'] < 0.1
```

## 📚 Práticas de Documentação

### 1. Docstrings Completas

```python
def analyze_query_performance(
    query: str,
    threshold_ms: float = 1000.0,
    include_io_stats: bool = False
) -> PerformanceReport:
    """
    Analyze query performance and provide optimization suggestions.
    
    This function executes EXPLAIN ANALYZE on the provided query and
    interprets the results to identify performance bottlenecks.
    
    Args:
        query: The SQL query to analyze. Must be a SELECT statement.
        threshold_ms: Performance threshold in milliseconds. Queries
            exceeding this are flagged as slow. Defaults to 1000ms.
        include_io_stats: Whether to include I/O statistics in analysis.
            Requires additional permissions. Defaults to False.
    
    Returns:
        PerformanceReport containing:
            - execution_time: Actual execution time in ms
            - planning_time: Query planning time in ms
            - bottlenecks: List of identified performance issues
            - suggestions: List of optimization suggestions
            - confidence: Confidence level of suggestions (0-1)
    
    Raises:
        ValidationError: If query is not a SELECT statement
        DatabaseError: If query execution fails
        PermissionError: If user lacks EXPLAIN permissions
    
    Examples:
        >>> report = analyze_query_performance(
        ...     "SELECT * FROM users WHERE email LIKE '%@gmail.com'",
        ...     threshold_ms=500
        ... )
        >>> print(report.suggestions)
        ['Consider using a GIN index for pattern matching']
    
    Note:
        This function executes the actual query with EXPLAIN ANALYZE,
        which can impact performance on production systems. Use with
        caution on large datasets.
    """
```

### 2. README Sections

```markdown
## Quick Start (30 seconds)
[Imediato, sem fricção]

## Features
[Lista clara de capacidades]

## Installation
[Múltiplas opções]

## Usage Examples
[Casos reais, não triviais]

## API Reference
[Completa mas concisa]

## Troubleshooting
[Problemas comuns e soluções]

## Contributing
[Como ajudar]
```

### 3. Changelog Semântico

```markdown
# Changelog

## [2.0.0] - 2025-05-31
### Added
- explain-query tool with automatic suggestions
- get-slow-queries tool with pg_stat_statements support
- health-check tool with comprehensive monitoring

### Changed
- Refactored handlers to async/await pattern
- Improved error messages with specific solutions

### Fixed
- Connection pool exhaustion under high load
- Quote handling for table names with special characters

### Security
- Added SQL injection prevention for dynamic queries
- Implemented read-only mode by default
```

## 🎓 Aprendizados Contínuos

### 1. Colete Feedback

```python
# Adicione telemetria opcional
def log_usage_stats(tool: str, success: bool, duration_ms: float):
    """Log anonymous usage statistics."""
    if not TELEMETRY_ENABLED:
        return
        
    stats = {
        'tool': tool,
        'success': success,
        'duration_ms': duration_ms,
        'version': __version__,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    # Send to analytics service
    send_telemetry(stats)
```

### 2. Iterate Baseado em Dados

```python
# Analise padrões de uso
most_used_tools = analyze_tool_usage()
slowest_queries = analyze_query_performance()
common_errors = analyze_error_patterns()

# Priorize melhorias
next_features = prioritize_by_impact(
    user_requests,
    usage_patterns,
    performance_data
)
```

### 3. Mantenha-se Atualizado

```bash
# Dependências
pip list --outdated
pip-audit

# PostgreSQL features
SELECT version();
SELECT * FROM pg_available_extensions;
```

## 🏁 Conclusão

Seguindo estas melhores práticas, o PostgreSQL MCP continuará sendo:
- **Confiável**: Funciona sempre que necessário
- **Performático**: Rápido mesmo sob carga
- **Seguro**: Protegido por design
- **Útil**: Resolve problemas reais
- **Manutenível**: Fácil de evoluir

---

*"O código bom é como uma piada boa: não precisa ser explicado."*

*Melhores Práticas v1.0 - PostgreSQL MCP v2.0* ⭐