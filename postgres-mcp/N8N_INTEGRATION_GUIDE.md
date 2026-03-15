# Guia de Integração PostgreSQL MCP com n8n

## 📋 Visão Geral

Este guia documenta como integrar o PostgreSQL MCP Server com o n8n para monitoramento e gerenciamento de bancos de dados PostgreSQL.

## 🏗️ Arquitetura

Temos 3 opções de integração:

### 1. HTTP REST API (Recomendado ✅)
- **URL**: https://postgres-sse.agentesintegrados.com
- **Autenticação**: Bearer Token
- **Protocolo**: HTTP REST + SSE
- **Porta**: 443 (HTTPS)

### 2. MCP over HTTP (Para MCP Client)
- **URL**: http://localhost:8082/mcp
- **Protocolo**: MCP JSON-RPC 2.0
- **Porta**: 8082

### 3. MCP Stdio (Local)
- **Comando**: `/root/.claude/postgres-mcp/start_postgres_mcp.sh`
- **Protocolo**: MCP via stdio

## 🔐 Configuração de Autenticação

### Token Bearer
```
Bearer EYjpWqb7YS1kJ0TKdJtVRN7Zj654NZbq6Ewe7RCHtPs
```

### Variáveis de Ambiente
```bash
export DATABASE_URI="postgresql://user:pass@host:port/database"
export POSTGRES_SSE_TOKEN="EYjpWqb7YS1kJ0TKdJtVRN7Zj654NZbq6Ewe7RCHtPs"
```

## 🚀 Configuração no n8n

### Opção 1: HTTP Request Node (Recomendado)

#### 1. Configuração Base
```json
{
  "authentication": "genericCredentialType",
  "genericAuthType": "httpHeaderAuth",
  "sendHeaders": true,
  "headerParameters": {
    "parameters": [
      {
        "name": "Authorization",
        "value": "Bearer EYjpWqb7YS1kJ0TKdJtVRN7Zj654NZbq6Ewe7RCHtPs"
      }
    ]
  }
}
```

#### 2. Endpoints Disponíveis

##### Listar Schemas
- **Method**: GET
- **URL**: `https://postgres-sse.agentesintegrados.com/api/list-schemas`

##### Listar Tabelas
- **Method**: GET
- **URL**: `https://postgres-sse.agentesintegrados.com/api/list-tables?schema=public`

##### Executar Query
- **Method**: POST
- **URL**: `https://postgres-sse.agentesintegrados.com/api/execute-query`
- **Body**:
```json
{
  "query": "SELECT * FROM tabela LIMIT 10"
}
```

##### Health Check
- **Method**: GET
- **URL**: `https://postgres-sse.agentesintegrados.com/api/health-check`

##### Queries Lentas
- **Method**: GET
- **URL**: `https://postgres-sse.agentesintegrados.com/api/slow-queries?min_duration_ms=1000&limit=20`

### Opção 2: MCP Client Node (Se disponível)

#### Configuração
- **Server URL**: `http://localhost:8082/mcp`
- **Transport**: HTTP
- **Protocol**: MCP

#### Ferramentas Disponíveis
- `postgres.test_connection`
- `postgres.list_schemas`
- `postgres.list_tables`
- `postgres.execute_query`
- `postgres.health_check`

## 📊 Exemplos de Workflows

### 1. Monitor de Saúde do Banco

```json
{
  "name": "PostgreSQL Health Monitor",
  "nodes": [
    {
      "name": "Every 5 minutes",
      "type": "n8n-nodes-base.schedule",
      "parameters": {
        "rule": {
          "interval": [{ "field": "minutes", "minutesInterval": 5 }]
        }
      }
    },
    {
      "name": "Check DB Health",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "method": "GET",
        "url": "https://postgres-sse.agentesintegrados.com/api/health-check",
        "authentication": "genericCredentialType",
        "genericAuthType": "httpHeaderAuth",
        "sendHeaders": true,
        "headerParameters": {
          "parameters": [{
            "name": "Authorization",
            "value": "Bearer EYjpWqb7YS1kJ0TKdJtVRN7Zj654NZbq6Ewe7RCHtPs"
          }]
        }
      }
    },
    {
      "name": "If Unhealthy",
      "type": "n8n-nodes-base.if",
      "parameters": {
        "conditions": {
          "string": [{
            "value1": "={{$json.health}}",
            "operation": "contains",
            "value2": "WARNING"
          }]
        }
      }
    },
    {
      "name": "Send Alert",
      "type": "n8n-nodes-base.telegram",
      "parameters": {
        "text": "⚠️ PostgreSQL Alert!\n\n{{$json.health}}",
        "chatId": "YOUR_CHAT_ID"
      }
    }
  ]
}
```

### 2. Backup de Queries Importantes

```json
{
  "name": "Backup Chat Memory Daily",
  "nodes": [
    {
      "name": "Daily at midnight",
      "type": "n8n-nodes-base.schedule",
      "parameters": {
        "rule": {
          "interval": [{ 
            "field": "cronExpression",
            "expression": "0 0 * * *"
          }]
        }
      }
    },
    {
      "name": "Get Chat Messages",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "method": "POST",
        "url": "https://postgres-sse.agentesintegrados.com/api/execute-query",
        "sendBody": true,
        "bodyParameters": {
          "parameters": [{
            "name": "query",
            "value": "SELECT * FROM chat_memory WHERE created_at >= NOW() - INTERVAL '24 hours'"
          }]
        },
        "authentication": "genericCredentialType",
        "genericAuthType": "httpHeaderAuth",
        "sendHeaders": true,
        "headerParameters": {
          "parameters": [{
            "name": "Authorization",
            "value": "Bearer EYjpWqb7YS1kJ0TKdJtVRN7Zj654NZbq6Ewe7RCHtPs"
          }]
        }
      }
    },
    {
      "name": "Save to Google Drive",
      "type": "n8n-nodes-base.googleDrive",
      "parameters": {
        "operation": "upload",
        "name": "chat_backup_{{$now.format('yyyy-MM-dd')}}.json",
        "binaryData": false,
        "fileContent": "={{JSON.stringify($json, null, 2)}}"
      }
    }
  ]
}
```

### 3. Monitor de Performance

```json
{
  "name": "PostgreSQL Performance Monitor",
  "nodes": [
    {
      "name": "Every hour",
      "type": "n8n-nodes-base.schedule",
      "parameters": {
        "rule": {
          "interval": [{ "field": "hours", "hoursInterval": 1 }]
        }
      }
    },
    {
      "name": "Get Slow Queries",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "method": "GET",
        "url": "https://postgres-sse.agentesintegrados.com/api/slow-queries?min_duration_ms=5000",
        "authentication": "genericCredentialType",
        "genericAuthType": "httpHeaderAuth",
        "sendHeaders": true,
        "headerParameters": {
          "parameters": [{
            "name": "Authorization",
            "value": "Bearer EYjpWqb7YS1kJ0TKdJtVRN7Zj654NZbq6Ewe7RCHtPs"
          }]
        }
      }
    },
    {
      "name": "Format Report",
      "type": "n8n-nodes-base.code",
      "parameters": {
        "language": "javaScript",
        "jsCode": "const queries = $input.all()[0].json;\nconst report = `📊 PostgreSQL Performance Report\n\nSlow Queries Found: ${queries.slow_queries?.length || 0}\n\n${queries.slow_queries || 'No slow queries detected'}`;\n\nreturn [{json: {report}}];"
      }
    },
    {
      "name": "Send Report",
      "type": "n8n-nodes-base.emailSend",
      "parameters": {
        "toEmail": "admin@example.com",
        "subject": "PostgreSQL Performance Report",
        "text": "={{$json.report}}"
      }
    }
  ]
}
```

## 🔍 Debugging

### Testar Conexão Manual
```bash
# Via cURL
curl -H "Authorization: Bearer EYjpWqb7YS1kJ0TKdJtVRN7Zj654NZbq6Ewe7RCHtPs" \
     https://postgres-sse.agentesintegrados.com/api/health-check

# Via n8n Execute Command
curl -H "Authorization: Bearer TOKEN" https://postgres-sse.agentesintegrados.com/api/list-schemas
```

### Verificar Servidores
```bash
# SSE Server (porta 8081)
ps aux | grep sse_server

# MCP TCP Server (porta 8082)
ps aux | grep mcp_tcp_server

# Logs
tail -f /root/.claude/postgres-mcp/sse_server.log
tail -f /root/.claude/postgres-mcp/mcp_tcp_server.log
```

## 🛡️ Segurança

1. **Token Bearer**: Sempre use HTTPS em produção
2. **Firewall**: Considere restringir acesso às portas 8081/8082
3. **Rate Limiting**: Configure no Caddy se necessário
4. **Logs**: Monitore acessos não autorizados

## 📚 Recursos Adicionais

- [Documentação n8n HTTP Request](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.httprequest/)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [PostgreSQL Performance Tuning](https://wiki.postgresql.org/wiki/Performance_Optimization)

## 🤝 Suporte

Para problemas ou dúvidas:
1. Verifique os logs dos servidores
2. Teste manualmente com cURL
3. Confirme que o DATABASE_URI está correto
4. Verifique se o token está válido