# PostgreSQL MCP Server - Documentação Completa

## 📋 Índice
- [Visão Geral](#visão-geral)
- [Arquitetura](#arquitetura)
- [URLs e Endpoints](#urls-e-endpoints)
- [Autenticação](#autenticação)
- [Instalação](#instalação)
- [Configuração](#configuração)
- [Uso com n8n](#uso-com-n8n)
- [API Reference](#api-reference)
- [Exemplos](#exemplos)
- [Troubleshooting](#troubleshooting)

## 🎯 Visão Geral

O PostgreSQL MCP Server é uma solução híbrida que oferece:
- **Protocolo MCP** (Model Context Protocol) para integração com ferramentas AI
- **API REST** para acesso HTTP tradicional
- **Server-Sent Events (SSE)** para monitoramento em tempo real
- **Autenticação Bearer Token** para segurança

## 🏗️ Arquitetura

```
PostgreSQL MCP Server
├── Servidor MCP (porta 8082)
│   ├── Protocolo: JSON-RPC 2.0
│   ├── URL Externa: https://postgres-server.agentesintegrados.com
│   └── Integração: n8n, Claude, outras ferramentas MCP
└── Servidor SSE (porta 8081)
    ├── Protocolo: REST + SSE
    ├── URL Externa: https://postgres-sse.agentesintegrados.com
    └── Uso: Dashboards, monitoramento real-time
```

## 🌐 URLs e Endpoints

### URL Principal
```
https://postgres-server.agentesintegrados.com
```

### Endpoints MCP (JSON-RPC)

#### POST /mcp
Endpoint principal para comunicação MCP.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "tools/list",
  "params": {},
  "id": 1
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "tools": [...]
  },
  "id": 1
}
```

### Endpoints SSE (Server-Sent Events)

#### GET /sse/health-check
Monitoramento contínuo da saúde do banco.

#### GET /sse/monitor-queries
Stream de queries em execução.

#### GET /sse/monitor-locks
Monitoramento de bloqueios em tempo real.

#### GET /sse/test-connection
Status da conexão em tempo real.

## 🔐 Autenticação

### Bearer Token
```
Authorization: Bearer EYjpWqb7YS1kJ0TKdJtVRN7Zj654NZbq6Ewe7RCHtPs
```

### Configurar Token Customizado
```bash
export POSTGRES_MCP_TOKEN="seu_token_aqui"
export POSTGRES_SSE_TOKEN="seu_token_aqui"
```

## 📦 Instalação

### 1. Clonar ou Baixar
```bash
cd /root/.claude
git clone <repository> postgres-mcp
cd postgres-mcp
```

### 2. Instalar Dependências
```bash
pip install aiohttp aiohttp-sse aiohttp-cors psycopg psycopg-binary mcp
```

### 3. Configurar Variáveis
```bash
export DATABASE_URI="postgresql://user:pass@host:port/database"
export POSTGRES_MCP_TOKEN="EYjpWqb7YS1kJ0TKdJtVRN7Zj654NZbq6Ewe7RCHtPs"
```

## ⚙️ Configuração

### Como Serviço (systemd)

#### 1. Criar arquivo de serviço
```bash
sudo tee /etc/systemd/system/postgres-mcp.service << EOF
[Unit]
Description=PostgreSQL MCP Server
After=network.target postgresql.service

[Service]
Type=simple
User=root
WorkingDirectory=/root/.claude/postgres-mcp
Environment="DATABASE_URI=postgresql://user:pass@localhost:port/database"
Environment="POSTGRES_MCP_TOKEN=EYjpWqb7YS1kJ0TKdJtVRN7Zj654NZbq6Ewe7RCHtPs"
ExecStart=/usr/bin/python3 /root/.claude/postgres-mcp/mcp_simple_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
```

#### 2. Habilitar e iniciar
```bash
sudo systemctl daemon-reload
sudo systemctl enable postgres-mcp
sudo systemctl start postgres-mcp
```

### Configuração Caddy
O arquivo Caddyfile já está configurado com:
- Proxy reverso para localhost:8082
- Headers CORS
- Suporte SSE
- Logs estruturados

## 🔧 Uso com n8n

### Configuração MCP Client

1. **Adicionar MCP Client node**
2. **Configurar:**
   - Server URL: `https://postgres-server.agentesintegrados.com/mcp`
   - Transport: HTTP
   - Auth: Bearer Token (opcional)

### Configuração HTTP Request

Para usar sem MCP Client:

```json
{
  "method": "POST",
  "url": "https://postgres-server.agentesintegrados.com/mcp",
  "authentication": "genericCredentialType",
  "genericAuthType": "httpHeaderAuth",
  "sendHeaders": true,
  "headerParameters": {
    "parameters": [
      {
        "name": "Authorization",
        "value": "Bearer EYjpWqb7YS1kJ0TKdJtVRN7Zj654NZbq6Ewe7RCHtPs"
      },
      {
        "name": "Content-Type",
        "value": "application/json"
      }
    ]
  },
  "sendBody": true,
  "specifyBody": "json",
  "jsonBody": {
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "postgres.list_schemas",
      "arguments": {}
    },
    "id": 1
  }
}
```

## 📚 API Reference

### Métodos MCP Disponíveis

#### initialize
Inicializa a sessão MCP.

#### tools/list
Lista todas as ferramentas disponíveis.

#### tools/call
Executa uma ferramenta específica.

### Ferramentas Disponíveis

#### postgres.test_connection
Testa a conexão com o banco de dados.

**Parâmetros:**
- `database_url` (opcional): String de conexão PostgreSQL

#### postgres.list_schemas
Lista todos os schemas do banco.

#### postgres.list_tables
Lista tabelas de um schema.

**Parâmetros:**
- `schema` (opcional): Nome do schema (padrão: "public")

#### postgres.execute_query
Executa uma query SQL.

**Parâmetros:**
- `query` (obrigatório): Query SQL para executar

#### postgres.health_check
Verifica a saúde do banco de dados.

## 💡 Exemplos

### cURL - Listar Ferramentas
```bash
curl -X POST https://postgres-server.agentesintegrados.com/mcp \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer EYjpWqb7YS1kJ0TKdJtVRN7Zj654NZbq6Ewe7RCHtPs" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/list",
    "params": {},
    "id": 1
  }'
```

### cURL - Executar Query
```bash
curl -X POST https://postgres-server.agentesintegrados.com/mcp \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer EYjpWqb7YS1kJ0TKdJtVRN7Zj654NZbq6Ewe7RCHtPs" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "postgres.execute_query",
      "arguments": {
        "query": "SELECT COUNT(*) FROM pg_stat_activity"
      }
    },
    "id": 2
  }'
```

### JavaScript - SSE
```javascript
const token = 'EYjpWqb7YS1kJ0TKdJtVRN7Zj654NZbq6Ewe7RCHtPs';
const eventSource = new EventSource(
  'https://postgres-server.agentesintegrados.com/sse/health-check',
  {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  }
);

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Health update:', data);
};

eventSource.onerror = (error) => {
  console.error('SSE error:', error);
};
```

### Python - Requests
```python
import requests
import json

url = "https://postgres-server.agentesintegrados.com/mcp"
headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer EYjpWqb7YS1kJ0TKdJtVRN7Zj654NZbq6Ewe7RCHtPs"
}

# Listar schemas
payload = {
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
        "name": "postgres.list_schemas",
        "arguments": {}
    },
    "id": 1
}

response = requests.post(url, headers=headers, data=json.dumps(payload))
print(response.json())
```

## 🔍 Troubleshooting

### Servidor não inicia
```bash
# Verificar logs
journalctl -u postgres-mcp -f

# Verificar se porta está em uso
lsof -i :8082
```

### Erro de conexão com banco
```bash
# Testar conexão diretamente
psql $DATABASE_URI -c "SELECT 1"

# Verificar variável de ambiente
echo $DATABASE_URI
```

### Token não funciona
```bash
# Verificar token configurado
cat /root/.claude/postgres-mcp/mcp_simple_server.log | grep Token

# Reconfigurar token
export POSTGRES_MCP_TOKEN="novo_token"
systemctl restart postgres-mcp
```

### SSE não conecta
- Verificar se o Caddy está rodando
- Confirmar que o SSL está funcionando
- Testar localmente primeiro: `curl http://localhost:8080/sse/health-check`

## 📊 Monitoramento

### Status do serviço
```bash
systemctl status postgres-mcp
```

### Logs em tempo real
```bash
journalctl -u postgres-mcp -f
```

### Métricas de uso
```bash
# Ver conexões ativas
curl -s -X POST https://postgres-server.agentesintegrados.com/mcp \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TOKEN" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "postgres.execute_query",
      "arguments": {
        "query": "SELECT COUNT(*) as active_connections FROM pg_stat_activity"
      }
    },
    "id": 1
  }'
```

## 🛡️ Segurança

### Boas Práticas
1. **Use tokens fortes** - Gere com `openssl rand -base64 32`
2. **HTTPS sempre** - Nunca use HTTP em produção
3. **Firewall** - Bloqueie portas 8081/8082 externamente
4. **Logs** - Monitore acessos não autorizados
5. **Rotate tokens** - Mude periodicamente

### Configuração de Firewall
```bash
# Bloquear acesso direto às portas
ufw deny 8081/tcp
ufw deny 8082/tcp
```

## 📞 Suporte

Para problemas ou dúvidas:
1. Verifique os logs do sistema
2. Consulte a documentação do MCP: https://modelcontextprotocol.io
3. Abra uma issue no repositório

## 📝 Licença

Este projeto está sob a licença MIT.