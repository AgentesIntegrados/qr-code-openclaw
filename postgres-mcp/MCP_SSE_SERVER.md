# PostgreSQL MCP SSE Server

Servidor MCP (Model Context Protocol) para PostgreSQL com transporte SSE (Server-Sent Events), seguindo a especificação oficial do protocolo MCP.

## Visão Geral

Este servidor implementa o protocolo MCP sobre HTTP+SSE, permitindo que clientes MCP (como n8n) se conectem e utilizem ferramentas PostgreSQL através de uma API padronizada.

## Arquitetura

### Protocolo MCP
- **Versão do Protocolo**: 2024-11-05
- **Transporte**: HTTP + SSE
- **Formato de Mensagens**: JSON-RPC 2.0

### Endpoints

1. **SSE Endpoint** (`/sse`)
   - Método: GET
   - Função: Canal de eventos server->client
   - Mantém conexão persistente para notificações

2. **Message Endpoint** (`/message`)
   - Método: POST
   - Função: Recebe mensagens client->server
   - Content-Type: application/json

3. **Health Endpoint** (`/health`)
   - Método: GET
   - Função: Verificação de saúde do servidor

## Ferramentas Disponíveis

### Ferramentas Básicas

#### test-connection
Testa a conexão com o banco PostgreSQL.
```json
{
  "name": "test-connection",
  "arguments": {
    "database_url": "postgresql://user:pass@host:port/db" // opcional
  }
}
```

#### list-schemas
Lista todos os schemas do banco de dados.
```json
{
  "name": "list-schemas",
  "arguments": {}
}
```

#### list-tables
Lista tabelas em um schema específico.
```json
{
  "name": "list-tables",
  "arguments": {
    "schema": "public" // padrão: public
  }
}
```

#### execute-query
Executa uma query SQL.
```json
{
  "name": "execute-query",
  "arguments": {
    "query": "SELECT * FROM users LIMIT 10"
  }
}
```

### Ferramentas de Performance

#### explain-query
Analisa o plano de execução de uma query.
```json
{
  "name": "explain-query",
  "arguments": {
    "query": "SELECT * FROM large_table",
    "analyze": false,  // executa a query para tempos reais
    "buffers": false,  // inclui estatísticas de buffer
    "format": "text"   // text, json, xml, yaml
  }
}
```

#### get-slow-queries
Obtém queries lentas do pg_stat_statements.
```json
{
  "name": "get-slow-queries",
  "arguments": {
    "limit": 20,
    "min_duration_ms": 1000
  }
}
```

#### health-check
Verificação completa da saúde do banco.
```json
{
  "name": "health-check",
  "arguments": {}
}
```

### Ferramentas de Otimização

#### suggest-indexes
Sugere índices baseado em padrões de queries.
```json
{
  "name": "suggest-indexes",
  "arguments": {
    "limit": 10,
    "min_calls": 10,
    "min_duration_ms": 100
  }
}
```

#### get-table-stats
Obtém estatísticas detalhadas de tabelas.
```json
{
  "name": "get-table-stats",
  "arguments": {
    "schema": "public",
    "table_pattern": "%",
    "include_indexes": true,
    "include_toast": false
  }
}
```

#### analyze-index-usage
Analisa uso de índices e identifica índices não utilizados.
```json
{
  "name": "analyze-index-usage",
  "arguments": {
    "schema": "public",
    "min_size_mb": 1,
    "days_unused": 30
  }
}
```

#### get-blocking-queries
Detecta queries que estão bloqueando outras.
```json
{
  "name": "get-blocking-queries",
  "arguments": {
    "min_duration_ms": 1000,
    "include_locks": true
  }
}
```

## Instalação e Configuração

### 1. Instalar Dependências
```bash
cd /root/.claude/postgres-mcp
pip install -r requirements.txt
```

### 2. Configurar Variáveis de Ambiente
```bash
export DATABASE_URI="postgresql://user:pass@localhost:5432/database"
```

### 3. Iniciar o Servidor

#### Desenvolvimento
```bash
./start_sse_server.sh
```

#### Produção (systemd)
```bash
# Copiar arquivo de serviço
sudo cp postgres-mcp-sse.service /etc/systemd/system/

# Recarregar systemd
sudo systemctl daemon-reload

# Iniciar serviço
sudo systemctl start postgres-mcp-sse

# Habilitar início automático
sudo systemctl enable postgres-mcp-sse
```

### 4. Configurar Nginx

```bash
# Copiar configuração
sudo cp nginx-postgres-sse.conf /etc/nginx/sites-available/postgres-sse.agentesintegrados.com

# Criar link simbólico
sudo ln -s /etc/nginx/sites-available/postgres-sse.agentesintegrados.com /etc/nginx/sites-enabled/

# Testar configuração
sudo nginx -t

# Recarregar Nginx
sudo systemctl reload nginx
```

## Uso com Clientes MCP

### Exemplo de Inicialização
```json
// Cliente -> Servidor
{
  "jsonrpc": "2.0",
  "method": "initialize",
  "params": {
    "clientInfo": {
      "name": "n8n",
      "version": "1.0.0"
    }
  },
  "id": "1"
}

// Servidor -> Cliente
{
  "jsonrpc": "2.0",
  "result": {
    "protocolVersion": "2024-11-05",
    "serverInfo": {
      "name": "postgres-mcp",
      "version": "1.0.0"
    },
    "capabilities": {
      "tools": {}
    }
  },
  "id": "1"
}
```

### Exemplo de Chamada de Ferramenta
```json
// Cliente -> Servidor
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "list-schemas",
    "arguments": {}
  },
  "id": "2"
}

// Servidor -> Cliente
{
  "jsonrpc": "2.0",
  "result": {
    "content": [
      {
        "type": "text",
        "text": "[{\"schema_name\": \"public\", ...}]"
      }
    ]
  },
  "id": "2"
}
```

## Monitoramento

### Logs
```bash
# Logs do serviço
sudo journalctl -u postgres-mcp-sse -f

# Logs personalizados
tail -f /var/log/postgres-mcp-sse.log
tail -f /var/log/postgres-mcp-sse.error.log
```

### Status do Serviço
```bash
sudo systemctl status postgres-mcp-sse
```

### Teste de Saúde
```bash
curl https://postgres-sse.agentesintegrados.com/health
```

## Segurança

### CORS
O servidor permite requisições de qualquer origem por padrão. Para produção, considere restringir no Nginx:

```nginx
# Restringir a domínios específicos
add_header Access-Control-Allow-Origin "https://n8n.example.com" always;
```

### SSL/TLS
O servidor deve ser acessado apenas via HTTPS em produção. A configuração Nginx inclui redirecionamento automático de HTTP para HTTPS.

### Autenticação
Atualmente não há autenticação implementada. Para ambientes de produção, considere adicionar:
- API Keys
- JWT
- Basic Auth via Nginx

## Troubleshooting

### Conexão SSE não mantida
- Verificar timeouts do Nginx
- Verificar logs de erro
- Testar com `curl`:
  ```bash
  curl -N https://postgres-sse.agentesintegrados.com/sse
  ```

### Erro de conexão com banco
- Verificar DATABASE_URI
- Testar conexão diretamente:
  ```bash
  psql $DATABASE_URI
  ```

### Ferramenta retorna erro
- Verificar logs do servidor
- Confirmar que extensões necessárias estão instaladas (ex: pg_stat_statements)
- Verificar permissões do usuário do banco