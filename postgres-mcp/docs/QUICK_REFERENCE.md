# 🚀 PostgreSQL MCP - Guia Rápido de Referência

## 🔧 Comandos Essenciais

### Reiniciar o MCP
```bash
claude mcp remove postgres-mcp -s user
claude mcp add postgres-mcp -s user -- /root/.claude/postgres-mcp/start_postgres_mcp.sh
```

### Verificar Status
```bash
claude mcp list | grep postgres
```

## 📋 Ferramentas Disponíveis

### 1️⃣ explain-query
```python
# Básico
explain-query(query="SELECT * FROM tabela WHERE campo = 'valor'")

# Com análise de performance real
explain-query(query="SELECT...", analyze=True)

# Com estatísticas de buffer
explain-query(query="SELECT...", analyze=True, buffers=True)

# Formato JSON
explain-query(query="SELECT...", format="json")
```

### 2️⃣ get-slow-queries
```python
# Padrão (queries > 1 segundo)
get-slow-queries()

# Customizado
get-slow-queries(min_duration_ms=500, limit=10)

# Queries muito rápidas mas frequentes
get-slow-queries(min_duration_ms=50, limit=50)
```

### 3️⃣ health-check
```python
# Verificação completa (sem parâmetros)
health-check()
```

## 🎯 Casos de Uso Comuns

### 🐌 "Minha aplicação está lenta"
```python
# 1. Verificar saúde geral
health-check()

# 2. Identificar queries lentas
get-slow-queries(min_duration_ms=100)

# 3. Analisar query específica
explain-query(query="[QUERY_LENTA]", analyze=True)
```

### 📈 "Preciso otimizar uma query"
```python
# 1. Analisar plano atual
explain-query(query="SELECT...", analyze=True, buffers=True)

# 2. Aplicar sugestões (índices, rewrites)

# 3. Comparar novo plano
explain-query(query="SELECT_OTIMIZADO...", analyze=True)
```

### 🏥 "Monitoramento de rotina"
```python
# Diário
health-check()

# Semanal
get-slow-queries(min_duration_ms=500, limit=50)
```

## 🚨 Interpretação Rápida

### Health Score
- **90-100**: 😊 Excelente
- **70-89**: 😐 Precisa atenção
- **< 70**: 😱 Ação imediata

### Cache Hit Ratio
- **> 99%**: 🎯 Perfeito
- **90-99%**: ✅ Bom
- **< 90%**: ⚠️ Aumentar shared_buffers

### Sequential Scans
- Em tabelas pequenas: ✅ OK
- Em tabelas grandes: ❌ Criar índice

### Query Time
- **< 100ms**: 🚀 Rápido
- **100-1000ms**: ⚠️ Monitorar
- **> 1000ms**: 🔴 Otimizar urgente

## 💡 Dicas Pro

### 1. Análise Incremental
```python
# Primeiro sem ANALYZE (plano estimado)
explain-query(query="SELECT...")

# Depois com ANALYZE (tempos reais)
explain-query(query="SELECT...", analyze=True)
```

### 2. Queries Complexas
```python
# Para queries muito grandes, salve em arquivo
query = """
WITH complex_cte AS (
    SELECT ...
)
SELECT ...
"""
explain-query(query=query, analyze=True)
```

### 3. Monitoramento Contínuo
```python
# Crie uma rotina
# 1. health-check() diário
# 2. get-slow-queries() semanal
# 3. explain-query() para novas features
```

## 🛠️ Troubleshooting

### "pg_stat_statements not found"
```sql
-- Como superuser
CREATE EXTENSION pg_stat_statements;
-- Reiniciar PostgreSQL pode ser necessário
```

### "Permission denied"
```sql
-- Garantir permissões
GRANT SELECT ON ALL TABLES IN SCHEMA pg_catalog TO seu_usuario;
```

### "No slow queries found"
```python
# Reduzir threshold
get-slow-queries(min_duration_ms=100)
# Ou verificar se pg_stat_statements está coletando
```

## 📊 Métricas Importantes

| Métrica | Valor Ideal | Ação se Fora |
|---------|------------|--------------|
| Conexões | < 80% máx | Aumentar max_connections |
| Cache Hit | > 95% | Aumentar shared_buffers |
| Dead Tuples | < 10% | VACUUM mais frequente |
| Idle in TX | < 5 | Revisar código da aplicação |
| Long Queries | 0 | Timeout ou otimização |

## 🎬 Workflow Completo

```python
# 1. Baseline
health = health-check()

# 2. Identificar problemas
if health_score < 90:
    slow = get-slow-queries(min_duration_ms=500)
    
# 3. Analisar top 3 queries
for query in top_3_slow_queries:
    plan = explain-query(query=query, analyze=True)
    
# 4. Implementar melhorias
# - Criar índices sugeridos
# - Reescrever queries
# - Ajustar configurações

# 5. Validar melhorias
new_health = health-check()
```

---

**PostgreSQL MCP v2.0** - Performance e Monitoramento Avançado
*Guia Rápido - Mantenha sempre à mão!*