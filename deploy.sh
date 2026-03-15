#!/bin/bash

# =========================================
# Script de Deploy - Disparador WhatsApp
# =========================================

set -e  # Parar se houver erro

echo "🚀 Iniciando deploy do Disparador WhatsApp..."

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Função para imprimir com cor
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# 1. Verificar se está no diretório correto
if [ ! -f "docker-compose.yml" ]; then
    print_error "Erro: docker-compose.yml não encontrado!"
    echo "Execute este script no diretório /home/plataforma/whatsapp/Disparador"
    exit 1
fi

# 2. Criar diretórios necessários
echo "📁 Criando diretórios..."
mkdir -p data/postgres data/redis data/uploads logs
print_success "Diretórios criados"

# 3. Copiar .env.example para .env se não existir
if [ ! -f ".env" ]; then
    echo "📝 Criando arquivo .env..."
    cp .env.example .env
    print_warning "Arquivo .env criado. Por favor, edite as configurações antes de usar em produção!"
else
    print_success "Arquivo .env já existe"
fi

# 4. Parar containers antigos
echo "🛑 Parando containers antigos..."
docker compose down 2>/dev/null || true
print_success "Containers parados"

# 5. Construir nova imagem
echo "🔨 Construindo imagem Docker..."
docker compose build --no-cache
print_success "Imagem construída"

# 6. Iniciar containers
echo "🚀 Iniciando containers..."
docker compose up -d
print_success "Containers iniciados"

# 7. Aguardar serviços ficarem prontos
echo "⏳ Aguardando serviços ficarem prontos..."
sleep 5

# Verificar health do PostgreSQL
echo -n "Verificando PostgreSQL... "
for i in {1..30}; do
    if docker compose exec -T postgres pg_isready -U disparador_user >/dev/null 2>&1; then
        print_success "PostgreSQL pronto!"
        break
    fi
    if [ $i -eq 30 ]; then
        print_error "PostgreSQL não está respondendo"
        exit 1
    fi
    sleep 2
done

# Verificar health do Redis
echo -n "Verificando Redis... "
if docker compose exec -T redis redis-cli ping >/dev/null 2>&1; then
    print_success "Redis pronto!"
else
    print_warning "Redis pode não estar configurado"
fi

# Verificar health da aplicação
echo -n "Verificando aplicação... "
for i in {1..30}; do
    if curl -f http://localhost:3000 >/dev/null 2>&1; then
        print_success "Aplicação pronta!"
        break
    fi
    if [ $i -eq 30 ]; then
        print_error "Aplicação não está respondendo"
        exit 1
    fi
    sleep 2
done

# 8. Mostrar status dos containers
echo ""
echo "📊 Status dos containers:"
docker compose ps

# 9. Verificar Caddy
if systemctl is-active --quiet caddy; then
    print_success "Caddy está rodando"
    echo ""
    echo "🌐 URLs disponíveis:"
    echo "   Local: http://localhost:3000"
    echo "   Produção: https://demo-disparador.agentesintegrados.com"
else
    print_warning "Caddy não está ativo. Execute: sudo systemctl reload caddy"
fi

# 10. Instruções finais
echo ""
echo "========================================="
echo -e "${GREEN}✨ Deploy concluído com sucesso!${NC}"
echo "========================================="
echo ""
echo "📝 Credenciais de acesso:"
echo "   Usuário: admin"
echo "   Senha: admin"
echo ""
echo "🔧 Comandos úteis:"
echo "   Ver logs: docker compose logs -f disparador"
echo "   Parar: docker compose down"
echo "   Reiniciar: docker compose restart"
echo "   Status: docker compose ps"
echo ""
echo "⚠️  IMPORTANTE: Em produção, altere as credenciais no arquivo .env"
echo ""