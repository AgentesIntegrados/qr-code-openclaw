# PostgreSQL MCP - Documentação Completa

## 📋 Índice

1. [Visão Geral](#visão-geral)
2. [Instalação](#instalação)
3. [Configuração](#configuração)
4. [Ferramentas Disponíveis](#ferramentas-disponíveis)
5. [Exemplos de Uso](#exemplos-de-uso)
6. [Arquitetura](#arquitetura)
7. [Troubleshooting](#troubleshooting)
8. [Desenvolvimento](#desenvolvimento)

## 🔍 Visão Geral

O PostgreSQL MCP é um servidor Model Context Protocol que permite ao Claude interagir com bancos de dados PostgreSQL de forma inteligente. Com ele, você pode executar queries, analisar performance, otimizar índices e monitorar a saúde do banco de dados através de comandos naturais.

### Características (v0.3.0)

- ✅ Execução segura de queries SQL
- ✅ Análise de performance e planos de execução
- ✅ Recomendações automáticas de índices
- ✅ Monitoramento de saúde do banco de dados
- ✅ Detecção de queries lentas
- ✅ Suporte para modo read-only ou unrestricted
- ✅ Análise de estatísticas de uso
- ✅ Otimização automática com IA

## 📦 Instalação

### Pré-requisitos

- Python 3.11 ou superior
- PostgreSQL 12+ (local ou remoto)
- Claude Code CLI (`claude`)

### Instalação Rápida

1. **Configure o ambiente**:
```bash
cd /root/.claude/postgres-mcp
./setup.sh
```

2. **Configure suas credenciais**:
```bash
cp .env.example .env
# Edite .env com suas credenciais PostgreSQL
nano .env
```

3. **Adicione ao Claude Code**:
```bash
claude mcp add postgres /root/.claude/postgres-mcp/start.sh
```

4. **Verifique a instalação**:
```bash
claude mcp list | grep postgres
```

### Instalação Manual

Se preferir instalar manualmente:

```bash
# Criar ambiente virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependências
pip install "mcp[cli]>=1.5.0" "psycopg[binary]>=3.2.6" humanize>=4.8.0 \
            pglast==7.2.0 attrs>=25.3.0 psycopg-pool>=3.2.6 instructor>=1.7.9

# Instalar em modo desenvolvimento
pip install -e .

# Adicionar ao Claude
claude mcp add postgres /root/.claude/postgres-mcp/start.sh
```

### Configuração do PostgreSQL

Se você não tem um PostgreSQL instalado:

```bash
# Instalar PostgreSQL
sudo apt-get update
sudo apt-get install -y postgresql postgresql-contrib

# Criar usuário e banco
sudo -u postgres psql << EOF
CREATE USER mcp_user WITH PASSWORD 'mcp_password';
CREATE DATABASE mcp_db OWNER mcp_user;
GRANT ALL PRIVILEGES ON DATABASE mcp_db TO mcp_user;
EOF
```

## 🔧 Configuração

### Arquivo .env

O postgres-mcp usa um arquivo `.env` para configuração:

```bash
# Conexão com o banco de dados
DATABASE_URI=postgresql://user:password@host:port/database

# Modo de acesso (opcional)
# - readonly: Apenas operações de leitura
# - unrestricted: Todas as operações (padrão)
ACCESS_MODE=unrestricted

# Configurações de pool de conexão (opcional)
POOL_MIN_SIZE=1
POOL_MAX_SIZE=10
POOL_TIMEOUT=30

# Timeout para queries (segundos)
QUERY_TIMEOUT=300
```

### Exemplos de DATABASE_URI

```bash
# Local com autenticação
DATABASE_URI=postgresql://postgres:senha@localhost:5432/meudb

# Remoto com SSL
DATABASE_URI=postgresql://user:pass@db.exemplo.com:5432/producao?sslmode=require

# Com schema específico
DATABASE_URI=postgresql://user:pass@localhost:5432/db?options=-csearch_path=myschema

# Socket Unix (local)
DATABASE_URI=postgresql://user:pass@/var/run/postgresql:5432/db
```

## 🛠️ Ferramentas Disponíveis

### Execução de SQL

#### 1. execute_sql
Executa queries SQL no banco de dados.

**Parâmetros**:
- `query` (obrigatório): Query SQL a executar
- `params`: Parâmetros para queries preparadas (opcional)

**Exemplo**:
```json
{
  "query": "SELECT * FROM users WHERE age > $1",
  "params": [18]
}
```

### Análise de Performance

#### 2. explain_query
Analisa o plano de execução de uma query.

**Parâmetros**:
- `query` (obrigatório): Query para analisar
- `analyze`: Executar EXPLAIN ANALYZE (padrão: false)
- `buffers`: Incluir informações de buffer (padrão: false)
- `format`: Formato de saída (text, json, xml, yaml)

**Exemplo**:
```json
{
  "query": "SELECT * FROM orders WHERE customer_id = 123",
  "analyze": true,
  "buffers": true,
  "format": "json"
}
```

#### 3. get_slow_queries
Obtém queries lentas do banco de dados.

**Parâmetros**:
- `min_duration`: Duração mínima em ms (padrão: 1000)
- `limit`: Número máximo de queries (padrão: 20)

### Otimização de Índices

#### 4. suggest_indexes
Sugere índices para otimizar performance.

**Parâmetros**:
- `table`: Tabela para analisar (opcional, analisa todas se omitido)
- `workload`: Lista de queries para considerar

**Exemplo**:
```json
{
  "table": "orders",
  "workload": [
    "SELECT * FROM orders WHERE customer_id = $1",
    "SELECT * FROM orders WHERE created_at > $1"
  ]
}
```

#### 5. analyze_index_usage
Analisa o uso atual de índices.

**Parâmetros**:
- `schema`: Schema para analisar (padrão: public)
- `include_unused`: Incluir índices não utilizados

### Monitoramento de Saúde

#### 6. health_check
Verifica a saúde geral do banco de dados.

**Retorna**:
- Status de conexões
- Uso de disco
- Cache hit ratio
- Estatísticas de vacuum
- Replicação (se configurada)
- Locks ativos

#### 7. get_table_stats
Obtém estatísticas detalhadas de tabelas.

**Parâmetros**:
- `schema`: Schema para analisar
- `table`: Tabela específica (opcional)

### Gerenciamento de Schema

#### 8. get_schema_info
Obtém informações sobre o schema do banco.

**Parâmetros**:
- `schema`: Nome do schema (padrão: public)
- `include_indexes`: Incluir índices
- `include_constraints`: Incluir constraints

## 📚 Exemplos de Uso

### Exemplo 1: Análise de Performance

```python
# Identificar queries lentas
slow_queries = await postgres.get_slow_queries(min_duration=5000)

# Analisar uma query específica
plan = await postgres.explain_query(
    query="SELECT * FROM orders WHERE status = 'pending'",
    analyze=True
)

# Sugerir índices
suggestions = await postgres.suggest_indexes(
    table="orders",
    workload=["SELECT * FROM orders WHERE status = $1"]
)
```

### Exemplo 2: Monitoramento

```python
# Health check completo
health = await postgres.health_check()

# Verificar uso de índices
index_usage = await postgres.analyze_index_usage(
    schema="public",
    include_unused=True
)

# Estatísticas de tabelas
stats = await postgres.get_table_stats(
    schema="public",
    table="orders"
)
```

### Exemplo 3: Execução Segura de SQL

```python
# Query com parâmetros (previne SQL injection)
result = await postgres.execute_sql(
    query="INSERT INTO logs (user_id, action) VALUES ($1, $2)",
    params=[123, "login"]
)

# Query de leitura
users = await postgres.execute_sql(
    query="SELECT id, name FROM users WHERE active = true"
)
```

## 🏗️ Arquitetura

### Componentes Principais

```
postgres-mcp/
├── src/postgres_mcp/
│   ├── __init__.py          # Entry point
│   ├── server.py            # MCP server principal
│   ├── sql/                 # Módulos SQL
│   │   ├── sql_driver.py    # Driver PostgreSQL
│   │   ├── safe_sql.py      # Validação de SQL
│   │   └── bind_params.py   # Binding de parâmetros
│   ├── database_health/     # Monitoramento
│   │   ├── health_calc.py   # Cálculos de saúde
│   │   └── metrics.py       # Métricas do banco
│   ├── index/               # Otimização de índices
│   │   ├── dta_calc.py      # Database Tuning Advisor
│   │   └── llm_opt.py       # Otimização com IA
│   └── explain/             # Análise de queries
│       └── explain_plan.py  # Parser de EXPLAIN
├── tests/                   # Testes unitários
├── pyproject.toml          # Configuração do projeto
└── .env                    # Configurações locais
```

### Fluxo de Dados

1. **Cliente (Claude)** → Envia comando MCP
2. **MCP Server** → Valida e roteia comando
3. **SQL Driver** → Conecta ao PostgreSQL
4. **PostgreSQL** → Executa operação
5. **Response Handler** → Formata resposta
6. **Cliente** ← Recebe resultado

### Pool de Conexões

O postgres-mcp usa um pool de conexões para melhor performance:

- Conexões reutilizáveis
- Limite configurável (POOL_MAX_SIZE)
- Timeout automático
- Retry em caso de falha

## 🔧 Troubleshooting

### Problema: "Connection failed"

**Causas comuns**:
1. PostgreSQL não está rodando
2. Credenciais incorretas
3. Firewall bloqueando conexão

**Soluções**:
```bash
# Verificar se PostgreSQL está rodando
sudo systemctl status postgresql

# Testar conexão
psql -h localhost -U user -d database

# Verificar logs
tail -f /var/log/postgresql/postgresql-*.log
```

### Problema: "Permission denied"

**Causa**: Usuário sem permissões adequadas

**Solução**:
```sql
-- Dar permissões completas
GRANT ALL PRIVILEGES ON DATABASE dbname TO username;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO username;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO username;
```

### Problema: "SSL required"

**Causa**: Servidor requer conexão SSL

**Solução**:
```bash
# Adicionar sslmode à URI
DATABASE_URI=postgresql://user:pass@host:5432/db?sslmode=require
```

### Logs de Debug

Para debug detalhado:

```bash
# Ativar logs verbose
export POSTGRES_MCP_DEBUG=true

# Ver logs do MCP
tail -f ~/.cache/claude-cli/mcp-logs-postgres/*.txt

# Logs do PostgreSQL
sudo tail -f /var/log/postgresql/postgresql-*.log
```

## 🚀 Desenvolvimento

### Estrutura de um Tool

```python
@server.tool()
async def my_new_tool(query: str, options: dict = None) -> list:
    """
    Descrição da ferramenta.
    
    Args:
        query: Query SQL ou parâmetro
        options: Opções adicionais
        
    Returns:
        Lista de resultados
    """
    async with db_connection.get_connection() as conn:
        result = await conn.execute(query)
        return format_result(result)
```

### Adicionando Novos Recursos

1. Crie o módulo em `src/postgres_mcp/`
2. Adicione o tool em `server.py`
3. Escreva testes em `tests/`
4. Atualize a documentação

### Testes

```bash
# Rodar todos os testes
pytest

# Teste específico
pytest tests/test_sql_driver.py

# Com coverage
pytest --cov=postgres_mcp
```

### Contribuindo

1. Fork o repositório
2. Crie uma branch: `git checkout -b feature/nova-funcionalidade`
3. Commit suas mudanças: `git commit -am 'Add nova funcionalidade'`
4. Push: `git push origin feature/nova-funcionalidade`
5. Crie um Pull Request

## 📝 Notas de Versão

### v0.3.0 (Atual)
- ✅ Suporte para Python 3.11+
- ✅ Pool de conexões assíncrono
- ✅ Análise de índices com IA
- ✅ Health check completo
- ✅ Modo read-only/unrestricted

### v0.2.0
- Análise de queries lentas
- Sugestões de índices básicas
- Melhorias de performance

### v0.1.0
- Versão inicial
- Execução básica de SQL
- EXPLAIN simples

## 🤝 Suporte

- **Issues**: [GitHub Issues](https://github.com/your-repo/postgres-mcp/issues)
- **Documentação**: Este arquivo
- **Comunidade**: Discord do Claude Code

## 📄 Licença

MIT License - veja LICENSE para detalhes.

---

**PostgreSQL MCP** - Tornando a interação com PostgreSQL mais inteligente 🐘🤖