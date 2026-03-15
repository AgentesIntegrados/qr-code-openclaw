#!/bin/bash
# Script wrapper para executar postgres-mcp via Docker
# Para uso com Claude Code

# Verificar se DATABASE_URI está definida
if [ -z "$DATABASE_URI" ]; then
    echo "Error: DATABASE_URI not set" >&2
    echo "Please set: export DATABASE_URI='postgresql://user:pass@host:port/db'" >&2
    exit 1
fi

# Executar container Docker
# -i: Mantém STDIN aberto (necessário para MCP)
# --rm: Remove container após execução
# --network host: Usa rede do host (para acessar PostgreSQL local)
docker run -i --rm \
    -e DATABASE_URI="${DATABASE_URI}" \
    --network host \
    postgres-mcp:latest