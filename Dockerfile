# Imagem base
FROM node:20-alpine

# Instalar curl
RUN apk add --no-cache curl dos2unix

# Diretório de trabalho
WORKDIR /app

# Criar diretório de uploads e definir permissões
RUN mkdir -p /app/public/uploads && \
    chmod 755 /app/public/uploads

# Copiar arquivos de dependências
COPY package*.json ./

# Instalar dependências
RUN npm install && \
    npm install --save-dev @typescript-eslint/parser @typescript-eslint/eslint-plugin && \
    npm install mime-types @types/mime-types libphonenumber-js

# Copiar todo o código fonte
COPY . .

# Criar e configurar o script de inicialização
RUN printf '#!/bin/sh\n\
echo "NEXT_PUBLIC_EVOLUTION_URL=$NEXT_PUBLIC_EVOLUTION_URL" > .env\n\
echo "NEXT_PUBLIC_EVOLUTION_API=$NEXT_PUBLIC_EVOLUTION_API" >> .env\n\
echo "NEXT_PUBLIC_APP_URL=$NEXT_PUBLIC_APP_URL" >> .env\n\
echo "NEXT_PUBLIC_AUTH_USERNAME=$AUTH_USERNAME" >> .env\n\
echo "NEXT_PUBLIC_AUTH_PASSWORD=$AUTH_PASSWORD" >> .env\n\
echo "AUTH_SECRET_KEY=$AUTH_SECRET_KEY" >> .env\n\
echo "DATABASE_URL=$DATABASE_URL" >> .env\n\
echo "NEXT_PUBLIC_CHATWOOT_INTEGRATION=$NEXT_PUBLIC_CHATWOOT_INTEGRATION" >> .env\n\
echo "NEXT_PUBLIC_CHATWOOT_DOMAIN=$NEXT_PUBLIC_CHATWOOT_DOMAIN" >> .env\n\
echo "NEXT_PUBLIC_CHATWOOT_ACCOUNT_ID=$NEXT_PUBLIC_CHATWOOT_ACCOUNT_ID" >> .env\n\
echo "NEXT_PUBLIC_CHATWOOT_TOKEN=$NEXT_PUBLIC_CHATWOOT_TOKEN" >> .env\n\
echo "NEXT_PUBLIC_CHATWOOT_DATABASE_CONNECTION_URI=$NEXT_PUBLIC_CHATWOOT_DATABASE_CONNECTION_URI" >> .env\n\
echo "NEXT_PUBLIC_AUTO_FILL_DDI=${NEXT_PUBLIC_AUTO_FILL_DDI:-true}" >> .env\n\
echo "NEXT_PUBLIC_DEFAULT_LOCATION=${NEXT_PUBLIC_DEFAULT_LOCATION:-BR}" >> .env\n\
npm run build\n\
npm start\n' > /app/start.sh

# Configurar script de entrada
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /app/start.sh /usr/local/bin/docker-entrypoint.sh && \
    dos2unix /usr/local/bin/docker-entrypoint.sh

# Limpar cache
RUN npm cache clean --force

# Expor a porta
EXPOSE 3000

# Volume para uploads
VOLUME ["/app/public/uploads"]

# Comando para iniciar a aplicação
ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["/app/start.sh"]
