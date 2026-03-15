# Exemplos de Uso - PostgreSQL MCP

Este documento demonstra como usar as novas ferramentas de performance e monitoramento do PostgreSQL MCP.

## 🚀 Ferramentas de Performance

### 1. explain-query - Análise de Planos de Execução

#### Exemplo Básico
```python
# Analisar plano de uma query simples
explain-query(query="SELECT * FROM users WHERE email = 'user@example.com'")
```

**Saída esperada:**
```
Query Execution Plan:
==================================================

Seq Scan on users  (cost=0.00..155.00 rows=1 width=200)
  Filter: (email = 'user@example.com'::text)

==================================================
Performance Analysis:

📌 Sequential scan on 'users'. May need an index if table is large.

--------------------------------------------------
💡 Tips:
• Run with analyze=True to see actual execution times
• Run with buffers=True to see buffer usage statistics
• Consider using EXPLAIN (VERBOSE) for more details
```

#### Exemplo com ANALYZE
```python
# Ver tempos reais de execução
explain-query(
    query="SELECT u.*, COUNT(m.id) as message_count 
           FROM users u 
           LEFT JOIN messages m ON m.user_id = u.id 
           GROUP BY u.id",
    analyze=True
)
```

**Saída esperada:**
```
Query Execution Plan:
==================================================

HashAggregate  (cost=450.00..460.00 rows=100 width=208) (actual time=15.234..15.567 rows=100 loops=1)
  Group Key: u.id
  ->  Hash Right Join  (cost=25.00..400.00 rows=10000 width=204) (actual time=0.456..12.345 rows=10000 loops=1)
        Hash Cond: (m.user_id = u.id)
        ->  Seq Scan on messages m  (cost=0.00..350.00 rows=10000 width=4) (actual time=0.123..8.901 rows=10000 loops=1)
        ->  Hash  (cost=20.00..20.00 rows=100 width=200) (actual time=0.234..0.234 rows=100 loops=1)
              Buckets: 128  Batches: 1  Memory Usage: 24kB
              ->  Seq Scan on users u  (cost=0.00..20.00 rows=100 width=200) (actual time=0.012..0.189 rows=100 loops=1)

Planning Time: 0.234 ms
Execution Time: 15.789 ms

==================================================
Performance Analysis:

📊 Timing Summary:
   - Planning Time: 0.23 ms
   - Execution Time: 15.79 ms
   - Total Time: 16.02 ms

✅ Using hash join - good for large datasets.
📌 Sequential scan on 'messages'. May need an index if table is large.
📌 Sequential scan on 'users'. May need an index if table is large.

--------------------------------------------------
💡 Tips:
• Run with buffers=True to see buffer usage statistics
• Consider using EXPLAIN (VERBOSE) for more details
```

#### Exemplo com BUFFERS
```python
# Análise completa com uso de buffers
explain-query(
    query="SELECT * FROM large_table WHERE status = 'active' ORDER BY created_at DESC LIMIT 100",
    analyze=True,
    buffers=True
)
```

### 2. get-slow-queries - Identificar Queries Lentas

#### Exemplo Básico
```python
# Buscar queries com tempo médio > 1 segundo
get-slow-queries()
```

**Saída esperada:**
```
Slow Queries Report (threshold: 1000ms)
================================================================================

🔴 Query #1
Query: SELECT COUNT(*) FROM messages WHERE content LIKE '%search_term%'
Performance Stats:
  • Calls: 5,234
  • Mean Time: 2345.67 ms
  • Total Time: 12276783.78 ms (12276.78 seconds)
  • Min/Max: 1234.56 ms / 4567.89 ms
  • Std Dev: 890.12 ms
  • Rows/Call: 1.0
  • Cache Hit: 65.3%

📊 Analysis:
• Leading wildcard in LIKE - cannot use index effectively
• Low cache hit ratio (65.3%) - consider increasing shared_buffers
• Very frequent execution - consider caching or query optimization

--------------------------------------------------------------------------------

🔴 Query #2
Query: SELECT DISTINCT user_id FROM activity_logs WHERE created_at > $1
Performance Stats:
  • Calls: 1,234
  • Mean Time: 1567.89 ms
  • Total Time: 1934693.46 ms (1934.69 seconds)
  • Min/Max: 987.65 ms / 2345.67 ms
  • Std Dev: 456.78 ms
  • Rows/Call: 234.5
  • Cache Hit: 89.2%

📊 Analysis:
• DISTINCT can be expensive - ensure proper indexes
• Returning many rows per call - consider pagination or more selective filters

--------------------------------------------------------------------------------

📈 Summary:
• Found 2 slow queries
• Threshold: 1000ms mean execution time
• Tip: Use explain-query tool to analyze specific queries in detail
```

#### Exemplo com Parâmetros Customizados
```python
# Buscar queries mais rápidas (> 500ms) e limitar a 5 resultados
get-slow-queries(min_duration_ms=500, limit=5)
```

### 3. health-check - Verificação Completa de Saúde

#### Exemplo de Uso
```python
# Executar verificação completa
health-check()
```

**Saída esperada:**
```
PostgreSQL Health Check Report
================================================================================

🔌 Connection Statistics:
  • Active connections: 15
  • Idle connections: 25
  • Idle in transaction: 2
  • Waiting connections: 0
  • Total connections: 42/100 (42.0% used)

💾 Database Size:
  • Current size: 2.3 GB
  • Top 5 largest tables:
    - public.messages: 1.2 GB
    - public.activity_logs: 456 MB
    - public.users: 123 MB
    - public.files: 89 MB
    - public.sessions: 45 MB

🎯 Cache Performance:
  • Cache hit ratio: 98.45%
  ✅ Good cache performance

🧹 Vacuum/Maintenance Status:
  • Tables with high dead tuple count:
    - public.messages: 5,234 dead tuples (2.1% of live)
    - public.activity_logs: 1,234 dead tuples (0.8% of live)

🔄 Replication Status:
  • Active replicas: 2
  ✅ All replicas in sync

⏱️  Long Running Queries:
  • PID 12345: Running for 00:08:23
    Query: SELECT * FROM generate_report($1, $2)...
  ⚠️  Consider investigating these queries

🎈 Potential Table Bloat:
  • public.messages: 1.2 GB (45% of total relation size)
  • public.users: 123 MB (38% of total relation size)
  💡 Low ratios may indicate index bloat

📊 Overall Health Summary:
  • Health Score: 85/100 ⚠️  GOOD (needs attention)
  • Issues found:
    - Long running queries detected

💡 Next Steps:
• Use get-slow-queries to identify performance bottlenecks
• Use explain-query to analyze problematic queries
• Monitor this health check regularly
```

## 🎯 Cenários de Uso Comum

### Cenário 1: Otimização de Query Lenta

1. **Identificar queries lentas:**
```python
get-slow-queries(min_duration_ms=500)
```

2. **Analisar plano de execução:**
```python
explain-query(
    query="[copiar query lenta aqui]",
    analyze=True,
    buffers=True
)
```

3. **Aplicar otimizações sugeridas**

### Cenário 2: Monitoramento de Rotina

1. **Verificar saúde geral:**
```python
health-check()
```

2. **Se score < 90, investigar queries:**
```python
get-slow-queries()
```

3. **Analisar queries problemáticas específicas**

### Cenário 3: Diagnóstico de Performance

1. **Query específica está lenta?**
```python
explain-query(query="SELECT ...", analyze=True)
```

2. **Verificar se é um padrão:**
```python
get-slow-queries(min_duration_ms=100, limit=50)
```

3. **Verificar saúde geral do banco:**
```python
health-check()
```

## 💡 Dicas Importantes

1. **Use `analyze=True` com cuidado** - ele executa a query real
2. **Para queries UPDATE/DELETE** - remova a parte de modificação e analise apenas o SELECT
3. **Cache hit ratio** - deve estar acima de 90% para boa performance
4. **Dead tuples** - acima de 20% indica necessidade de VACUUM
5. **pg_stat_statements** - precisa estar habilitado para get-slow-queries funcionar

## 🔧 Troubleshooting

### "pg_stat_statements not found"
```sql
-- Como DBA, execute:
CREATE EXTENSION pg_stat_statements;
```

### "Permission denied"
- Certifique-se que o usuário tem permissão SELECT nas tabelas pg_stat_*

### Query muito complexa para EXPLAIN
- Divida em partes menores
- Use CTEs (WITH clauses) para simplificar

## 📊 Interpretando Resultados

### Planos de Execução
- **Seq Scan**: Leitura sequencial - ruim para tabelas grandes
- **Index Scan**: Uso de índice - bom para queries seletivas
- **Bitmap Scan**: Múltiplas linhas via índice - eficiente
- **Hash Join**: Bom para grandes conjuntos
- **Nested Loop**: Pode ser lento com muitas linhas

### Métricas de Performance
- **Mean time > 1000ms**: Query definitivamente precisa otimização
- **Cache hit < 90%**: Aumentar shared_buffers
- **High std dev**: Performance inconsistente
- **Many calls**: Candidata para caching

### Health Score
- **90-100**: Excelente
- **70-89**: Bom, mas precisa atenção
- **< 70**: Ação imediata necessária