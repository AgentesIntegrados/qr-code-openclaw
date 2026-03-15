#!/bin/bash
# Script para iniciar o PostgreSQL MCP Server

# Navegar para o diretório do projeto
cd /root/.claude/postgres-mcp

# Ativar ambiente virtual
source venv/bin/activate

# Executar o servidor
exec python src/postgres_mcp/server_simple.py