#!/bin/bash
# Script de Teste das Novas Funcionalidades do PostgreSQL MCP
# Data: 31/05/2025

echo "========================================="
echo "🧪 Teste das Novas Ferramentas PostgreSQL MCP"
echo "========================================="
echo ""

# Cores para output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Verificar se DATABASE_URI está configurada
if [ -z "$DATABASE_URI" ]; then
    echo -e "${RED}❌ DATABASE_URI não configurada!${NC}"
    echo "Execute: export DATABASE_URI=\"postgresql://evo_user:evo_pass@localhost:5432/evolution_db\""
    exit 1
fi

echo -e "${GREEN}✅ DATABASE_URI configurada${NC}"
echo ""

# Função para testar comando Python
test_command() {
    local description=$1
    local command=$2
    
    echo -e "${YELLOW}📋 Testando: $description${NC}"
    echo "Comando: $command"
    echo "---"
    
    # Executar comando
    cd /root/.claude/postgres-mcp
    source venv/bin/activate
    
    python3 -c "$command"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Sucesso!${NC}"
    else
        echo -e "${RED}❌ Erro no teste${NC}"
    fi
    echo ""
}

# Teste 1: Importar handlers
test_command "Importação dos handlers" "
from handlers import PostgresHandlers
print('Handlers importados com sucesso')
print(f'Métodos disponíveis: {len([m for m in dir(PostgresHandlers) if m.startswith(\"handle_\")])}')"

# Teste 2: Verificar conexão
test_command "Conexão com banco de dados" "
import asyncio
from handlers import PostgresHandlers

async def test():
    result = await PostgresHandlers.handle_test_connection(None)
    print(result[0].text[:100])

asyncio.run(test())"

# Teste 3: Health Check básico
test_command "Health Check (primeiras linhas)" "
import asyncio
from handlers import PostgresHandlers

async def test():
    result = await PostgresHandlers.handle_health_check(None)
    lines = result[0].text.split('\\n')[:10]
    for line in lines:
        print(line)

asyncio.run(test())"

# Teste 4: Verificar ferramentas no servidor
test_command "Ferramentas registradas no servidor" "
import sys
sys.path.insert(0, '/root/.claude/postgres-mcp/src')
from postgres_mcp.server_simple import tools

print(f'Total de ferramentas: {len(tools)}')
for tool in tools:
    print(f'  - {tool.name}: {tool.description[:50]}...')"

echo "========================================="
echo "📊 Resumo dos Testes"
echo "========================================="
echo ""
echo "Se todos os testes passaram:"
echo "1. Os handlers estão funcionando ✅"
echo "2. A conexão com o banco está OK ✅"
echo "3. As novas ferramentas estão disponíveis ✅"
echo ""
echo "Para usar no Claude Code:"
echo "  - Reinicie o Claude Code"
echo "  - Use: postgres-mcp:health-check"
echo "  - Use: postgres-mcp:get-slow-queries"
echo "  - Use: postgres-mcp:explain-query(query=\"SELECT...\")"
echo ""
echo -e "${GREEN}🎉 Implementação da Fase 1 completa!${NC}"