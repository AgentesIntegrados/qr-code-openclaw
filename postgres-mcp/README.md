# PostgreSQL MCP Server

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

## Status: ✅ FUNCIONANDO COM NOVAS FERRAMENTAS! (31/05/2025)

Este servidor MCP para PostgreSQL foi reconstruído e **significativamente aprimorado** com ferramentas avançadas de performance e monitoramento.

## Overview

PostgreSQL MCP é um servidor Model Context Protocol (MCP) que permite interação com bancos de dados PostgreSQL através de ferramentas integradas.

### Características Principais

- 🔍 **Exploração de Schema** - Lista schemas, tabelas e estruturas do banco
- ⚡ **Execução de Queries** - Execute queries SELECT de forma segura
- 🚀 **Análise de Performance** - EXPLAIN com sugestões automáticas
- 📊 **Detecção de Queries Lentas** - Identifica gargalos automaticamente
- 🏥 **Health Check Completo** - Monitoramento 360° do banco
- 🛡️ **Modo Seguro** - Apenas queries de leitura são permitidas
- 🔌 **Fácil Integração** - Pronto para usar com Claude Code

## Instalação Rápida

### Opção 1: Instalação Local

```bash
claude mcp add postgres-mcp -s user -- /root/.claude/postgres-mcp/start_postgres_mcp.sh
```

### Opção 2: 🐳 Instalação via Docker (NOVO!)

```bash
# Build da imagem
cd /root/.claude/postgres-mcp
docker build -t postgres-mcp:latest .

# Adicionar ao Claude Code
claude mcp add postgres-mcp-docker -s user -- /root/.claude/postgres-mcp/start-docker-mcp.sh
```

Vantagens do Docker:
- ✅ Isolamento completo
- ✅ Sem conflitos de dependências
- ✅ Fácil atualização
- ✅ Portabilidade total

### 2. Configurar Conexão com o Banco

Configure a variável de ambiente DATABASE_URI:

```bash
# Para Evolution API PostgreSQL (principal):
export DATABASE_URI="postgresql://evo_user:evo_pass@localhost:5432/evolution_db"

# Para outros bancos PostgreSQL disponíveis:
# - Alexandre (porta 5433): postgresql://evo_user:evo_pass@localhost:5433/evolution_db
# - V4Company (porta 5434): postgresql://evo_user:evo_pass@localhost:5434/evolution_db
# - G4Educacao (porta 5435): postgresql://evo_user:evo_pass@localhost:5435/evolution_db
```

Ou adicione ao seu ~/.bashrc para configuração permanente:

```bash
echo 'export DATABASE_URI="postgresql://evo_user:evo_pass@localhost:5432/evolution_db"' >> ~/.bashrc
source ~/.bashrc
```

### 3. Reiniciar Claude Code

Após adicionar o MCP e configurar a DATABASE_URI, reinicie o Claude Code para carregar o servidor.

## Ferramentas Disponíveis

### 📋 Ferramentas Básicas

#### test-connection
Testa a conexão com o banco de dados PostgreSQL.

```
Uso: test-connection
Parâmetros:
  - database_url (opcional): String de conexão PostgreSQL
```

#### list-schemas
Lista todos os schemas disponíveis no banco de dados.

```
Uso: list-schemas
Retorna: Lista de schemas com tipo (User/System) e proprietário
```

#### list-tables
Lista todas as tabelas em um schema específico.

```
Uso: list-tables
Parâmetros:
  - schema (opcional): Nome do schema (padrão: "public")
Retorna: Lista de tabelas com número de colunas e tamanho
```

#### execute-query
Executa queries SQL no banco de dados (apenas SELECT permitido).

```
Uso: execute-query
Parâmetros:
  - query (obrigatório): Query SQL para executar
Retorna: Resultados da query formatados
```

### 🚀 Ferramentas de Performance (NOVO!)

#### explain-query
Analisa o plano de execução de queries usando EXPLAIN.

```
Uso: explain-query
Parâmetros:
  - query (obrigatório): Query SQL para analisar
  - analyze (opcional): Incluir estatísticas reais de execução (padrão: false)
  - buffers (opcional): Incluir uso de buffers (requer analyze=true, padrão: false)
  - format (opcional): Formato de saída - text, json, xml, yaml (padrão: "text")

Exemplo:
  explain-query(query="SELECT * FROM users WHERE id = 1", analyze=true)
  
Retorna: 
  - Plano de execução detalhado
  - Análise automática com sugestões
  - Identificação de problemas de performance
```

#### get-slow-queries
Identifica queries lentas usando pg_stat_statements.

```
Uso: get-slow-queries
Parâmetros:
  - min_duration_ms (opcional): Tempo mínimo de execução em ms (padrão: 1000)
  - limit (opcional): Número máximo de queries (padrão: 20)

Exemplo:
  get-slow-queries(min_duration_ms=500, limit=10)
  
Retorna:
  - Lista de queries lentas com estatísticas
  - Análise de padrões problemáticos
  - Sugestões de otimização específicas
```

#### health-check
Verificação completa da saúde do banco de dados.

```
Uso: health-check
Parâmetros: Nenhum

Retorna:
  - 🔌 Estatísticas de conexões
  - 💾 Tamanho do banco e tabelas
  - 🎯 Performance do cache
  - 🧹 Status de vacuum e manutenção
  - 🔄 Status de replicação
  - ⏱️ Queries de longa duração
  - 🎈 Detecção de bloat
  - 📊 Score de saúde geral
```

### 🎯 Ferramentas de Otimização (NOVO - 31/05/2025)

#### suggest-indexes
Analisa o workload de queries e sugere índices otimizados.

```
Uso: suggest-indexes
Parâmetros:
  - min_calls (opcional): Mínimo de chamadas para considerar query (padrão: 10)
  - min_duration_ms (opcional): Duração média mínima em ms (padrão: 100)
  - limit (opcional): Número máximo de queries para analisar (padrão: 10)

Exemplo:
  suggest-indexes(min_calls=5, min_duration_ms=50)

Retorna:
  - Análise de workload de queries
  - Sugestões de índices baseadas em padrões
  - Comandos CREATE INDEX prontos para uso
  - Fallback para análise estrutural se pg_stat_statements não disponível
```

#### get-table-stats
Coleta estatísticas detalhadas sobre tabelas do banco.

```
Uso: get-table-stats
Parâmetros:
  - schema (opcional): Nome do schema (padrão: "public")
  - table_pattern (opcional): Padrão LIKE para filtrar tabelas (padrão: "%")
  - include_toast (opcional): Incluir informações TOAST (padrão: false)
  - include_indexes (opcional): Incluir detalhes de índices (padrão: true)

Exemplo:
  get-table-stats(schema="public", table_pattern="user%")

Retorna:
  - 📋 Informações básicas da tabela
  - 💾 Estatísticas de armazenamento
  - 🔍 Detalhes de índices
  - 📈 Estatísticas de atividade
  - 🔧 Status de manutenção
  - 💡 Recomendações específicas
```

#### analyze-index-usage
Identifica índices não utilizados ou redundantes.

```
Uso: analyze-index-usage
Parâmetros:
  - schema (opcional): Nome do schema (padrão: "public")
  - min_size_mb (opcional): Tamanho mínimo do índice em MB (padrão: 1)
  - days_unused (opcional): Dias sem uso para sinalizar (padrão: 30)

Exemplo:
  analyze-index-usage(min_size_mb=10)

Retorna:
  - 🔴 Índices não utilizados
  - 🟡 Índices raramente usados
  - 🔄 Índices duplicados
  - 📏 Índices superdimensionados
  - 💰 Economia potencial de espaço
```

#### get-blocking-queries
Detecta queries que estão bloqueando outras.

```
Uso: get-blocking-queries
Parâmetros:
  - include_locks (opcional): Incluir informações de locks (padrão: true)
  - min_duration_ms (opcional): Duração mínima para queries longas (padrão: 1000)

Exemplo:
  get-blocking-queries(min_duration_ms=5000)

Retorna:
  - 🔴 Cadeias de bloqueio ativas
  - 🔐 Informações detalhadas de locks
  - ⏱️ Queries de longa duração
  - 💡 Opções de resolução (cancel/terminate)
```

#### table-bloat-analysis
Analisa bloat em tabelas e sugere ações de manutenção.

```
Uso: table-bloat-analysis
Parâmetros:
  - schema (opcional): Nome do schema (padrão: "public")
  - min_size_mb (opcional): Tamanho mínimo da tabela em MB (padrão: 10)
  - bloat_threshold (opcional): Percentual de bloat para alertar (padrão: 20)

Exemplo:
  table-bloat-analysis(bloat_threshold=30)

Retorna:
  - 🎈 Análise de bloat por tabela
  - 🛠️ Ações recomendadas por criticidade
  - ⚙️ Configurações de autovacuum
  - 📚 Melhores práticas de manutenção
```

## Estrutura do Projeto (Após Limpeza - 31/05/2025)

```
/root/.claude/postgres-mcp/
├── src/postgres_mcp/       # Código fonte principal
│   ├── __init__.py
│   ├── server_simple.py    # Servidor principal em uso
│   ├── database_health/    # Ferramentas de saúde do banco
│   ├── explain/            # Análise de planos de execução
│   ├── index/              # Otimização de índices
│   ├── sql/                # Utilitários SQL
│   └── top_queries/        # Análise de queries
├── handlers.py             # Handlers para operações PostgreSQL
├── start_postgres_mcp.sh   # Script de inicialização único
├── pyproject.toml          # Configuração do projeto
├── venv/                   # Ambiente virtual Python
├── assets/                 # Recursos visuais
├── .env                    # Configuração de conexão
├── README.md              # Este arquivo
└── backup_old/            # Arquivos antigos preservados
```

## Arquitetura

O servidor foi implementado seguindo o padrão do docker-mcp:

1. **Server Pattern**: Usa `mcp.server.Server` diretamente
2. **Handlers Separados**: Lógica de negócio em arquivo separado
3. **Comunicação stdio**: Usa `mcp.server.stdio.stdio_server()`
4. **Estrutura Simples**: Foco em funcionalidade e manutenibilidade

## Desenvolvimento

### Requisitos

- Python 3.11+
- PostgreSQL 
- psycopg (instalado automaticamente)

### Instalação para Desenvolvimento

```bash
cd /root/.claude/postgres-mcp
source venv/bin/activate
pip install -e .
```

### Executar em Modo Debug

```bash
cd /root/.claude/postgres-mcp
source venv/bin/activate
DATABASE_URI="postgresql://user:pass@localhost/db" python -m postgres_mcp
```

## Troubleshooting

### MCP não aparece no Claude Code

1. Verifique permissões do script:
```bash
chmod +x /root/.claude/postgres-mcp/start_postgres_mcp.sh
```

2. Teste manualmente:
```bash
/root/.claude/postgres-mcp/start_postgres_mcp.sh
```

3. Adicione ao Claude Code:
```bash
claude mcp add postgres-mcp -s user -- /root/.claude/postgres-mcp/start_postgres_mcp.sh
```

### postgres-mcp aparece como "failed" (NOVO - 06/01/2025)

Se o postgres-mcp aparecer como "failed" ao executar o comando `mcp`:

1. **Verifique se o módulo psycopg está instalado:**
```bash
cd /root/.claude/postgres-mcp
source venv/bin/activate
pip install psycopg psycopg-binary
```

2. **Reinicie o postgres-mcp no Claude Code:**
```bash
claude mcp remove postgres-mcp -s user
claude mcp add postgres-mcp -s user -- /root/.claude/postgres-mcp/start_postgres_mcp.sh
```

3. **Verifique os logs de erro:**
```bash
# Os logs estão em diretórios específicos por projeto
ls /root/.cache/claude-cli-nodejs/*/mcp-logs-postgres-mcp/
```

### Erro de conexão com banco

1. Verifique a DATABASE_URI:
```bash
echo $DATABASE_URI
```

2. Teste conexão com psql:
```bash
psql $DATABASE_URI -c "SELECT 1"
```

### Trabalhando com múltiplas instâncias PostgreSQL

Quando precisar alternar entre diferentes bancos PostgreSQL, você tem duas opções:

**Opção 1: Reiniciar o MCP com nova DATABASE_URI**
```bash
export DATABASE_URI="postgresql://user:pass@localhost:5437/dbname"
claude mcp remove postgres-mcp -s user
claude mcp add postgres-mcp -s user -- /root/.claude/postgres-mcp/start_postgres_mcp.sh
```

**Opção 2: Usar comandos diretos (mais rápido para múltiplas instâncias)**
```bash
# Útil quando precisa acessar várias instâncias sem reiniciar o MCP
psql -h localhost -p 5437 -U user -d dbname -c "SELECT * FROM table"
```

### Logs e Debug

Para ver logs detalhados, execute o servidor manualmente e observe a saída.

## Segurança

- Apenas queries SELECT são permitidas por padrão
- Conexões são gerenciadas com segurança via psycopg
- Credenciais devem ser protegidas (use variáveis de ambiente)

## Histórico de Mudanças

### 31/05/2025
- Reconstruído seguindo padrão docker-mcp
- Implementadas ferramentas básicas
- Testado e funcionando com Claude Code

## Monitoramento e Scripts Auxiliares

### Script de Status
```bash
/root/.claude/postgres-mcp/pg-mcp-status.sh
```

### Logs de Monitoramento
- Monitor: `/var/log/postgres-mcp-monitoring/monitor.log`
- Limpeza: `/var/log/postgres-mcp-monitoring/cleanup.log`
- Crescimento: `/var/log/postgres-mcp-monitoring/growth-history.csv`

## Suporte

Para problemas ou dúvidas, verifique:
1. Este README
2. Arquivo COMO_ADICIONAR_CLAUDE_CODE.md
3. Documentação em CLAUDE.md