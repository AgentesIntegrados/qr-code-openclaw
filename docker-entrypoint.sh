#!/bin/sh

# Criar/atualizar arquivo .env
echo "NEXT_PUBLIC_EVOLUTION_URL=$NEXT_PUBLIC_EVOLUTION_URL
NEXT_PUBLIC_EVOLUTION_API=$NEXT_PUBLIC_EVOLUTION_API
NEXT_PUBLIC_APP_URL=$NEXT_PUBLIC_APP_URL
NEXT_PUBLIC_AUTH_USERNAME=$AUTH_USERNAME
NEXT_PUBLIC_AUTH_PASSWORD=$AUTH_PASSWORD
AUTH_SECRET_KEY=$AUTH_SECRET_KEY
NEXT_PUBLIC_CHATWOOT_INTEGRATION=$NEXT_PUBLIC_CHATWOOT_INTEGRATION
NEXT_PUBLIC_CHATWOOT_DOMAIN=$NEXT_PUBLIC_CHATWOOT_DOMAIN
NEXT_PUBLIC_CHATWOOT_ACCOUNT_ID=$NEXT_PUBLIC_CHATWOOT_ACCOUNT_ID
NEXT_PUBLIC_CHATWOOT_TOKEN=$NEXT_PUBLIC_CHATWOOT_TOKEN
NEXT_PUBLIC_CHATWOOT_DATABASE_CONNECTION_URI=$NEXT_PUBLIC_CHATWOOT_DATABASE_CONNECTION_URI
NEXT_PUBLIC_AUTO_FILL_DDI=${NEXT_PUBLIC_AUTO_FILL_DDI:-true}
NEXT_PUBLIC_DEFAULT_LOCATION=${NEXT_PUBLIC_DEFAULT_LOCATION:-BR}" > .env

echo "
██████╗ ██╗███████╗██████╗  █████╗ ██████╗  █████╗ ██████╗  ██████╗ ██████╗ 
██╔══██╗██║██╔════╝██╔══██╗██╔══██╗██╔══██╗██╔══██╗██╔══██╗██╔═══██╗██╔══██╗
██║  ██║██║███████╗██████╔╝███████║██████╔╝███████║██║  ██║██║   ██║██████╔╝
██║  ██║██║╚════██║██╔═══╝ ██╔══██║██╔══██╗██╔══██║██║  ██║██║   ██║██╔══██╗
██████╔╝██║███████║██║     ██║  ██║██║  ██║██║  ██║██████╔╝╚██████╔╝██║  ██║
╚═════╝ ╚═╝╚══════╝╚═╝     ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝  ╚═════╝ ╚═╝  ╚═╝

 ██████╗ ██████╗ ██╗ ██████╗ ███╗   ██╗
██╔═══██╗██╔══██╗██║██╔═══██╗████╗  ██║
██║   ██║██████╔╝██║██║   ██║██╔██╗ ██║
██║   ██║██╔══██╗██║██║   ██║██║╚██╗██║
╚██████╔╝██║  ██║██║╚██████╔╝██║ ╚████║
 ╚═════╝ ╚═╝  ╚═╝╚═╝ ╚═════╝ ╚═╝  ╚═══╝
"

echo "================================================"
echo "🔧 Configurações do Ambiente:"
echo "------------------------------------------------"
echo "📡 API URL: $NEXT_PUBLIC_EVOLUTION_URL"
echo "🔑 API Key: ${NEXT_PUBLIC_EVOLUTION_API:0:8}..."
echo "🌐 App URL: $NEXT_PUBLIC_APP_URL"
echo "🔒 Node Environment: $NODE_ENV"
echo "🌍 Porta: 3000"
echo "================================================"

echo "\n🔍 Testando conexão com a API..."
API_RESPONSE=$(curl -s "$NEXT_PUBLIC_EVOLUTION_URL" || echo "failed")
API_STATUS=$(echo "$API_RESPONSE" | grep -o '"status":[0-9]*' | cut -d':' -f2)
API_VERSION=$(echo "$API_RESPONSE" | grep -o '"version":"[^"]*"' | cut -d'"' -f4)

if [ "$API_STATUS" = "200" ]; then
    echo "✅ API respondeu com sucesso (HTTP 200)"
    echo "📦 Versão da API: $API_VERSION"
elif [ "$API_RESPONSE" = "failed" ]; then
    echo "❌ Não foi possível conectar à API"
    echo "🔍 Tentando fazer um DNS lookup..."
    API_HOST=$(echo "$NEXT_PUBLIC_EVOLUTION_URL" | sed -e 's|^[^/]*//||' -e 's|/.*$||')
    nslookup "$API_HOST" || echo "❌ Falha no DNS lookup"
else
    echo "⚠️ API respondeu com status HTTP $API_STATUS"
fi

echo "\n✅ Iniciando o servidor Next.js..."
echo "================================================\n"

mkdir -p /app/public/uploads
chmod -R 755 /app/public/uploads
chown -R node:node /app/public/uploads

exec "$@"