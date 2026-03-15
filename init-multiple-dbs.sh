#!/bin/bash
set -e

# Criar múltiplos bancos de dados no PostgreSQL
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- Criar banco para o Disparador
    CREATE DATABASE disparador_db;
    GRANT ALL PRIVILEGES ON DATABASE disparador_db TO $POSTGRES_USER;
    
    -- Criar banco para o n8n (se não existir)
    CREATE DATABASE n8n_db;
    GRANT ALL PRIVILEGES ON DATABASE n8n_db TO $POSTGRES_USER;
    
    -- Conectar ao banco do disparador para criar o schema
    \c disparador_db;
    
    -- O init.sql será executado depois para criar as tabelas
EOSQL

echo "Múltiplos bancos de dados criados com sucesso!"