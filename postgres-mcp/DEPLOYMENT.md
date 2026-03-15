# Deployment Guide - PostgreSQL MCP SSE Server

## Visão Geral

Este guia detalha como implantar o PostgreSQL MCP SSE Server em produção.

## Status Atual

### ✅ Servidor SSE Implementado
- Localização: `/root/.claude/postgres-mcp/src/postgres_mcp/server_sse.py`
- Protocolo: MCP sobre HTTP+SSE (Server-Sent Events)
- Formato: JSON-RPC 2.0
- Porta padrão: 8000

### ✅ Serviço Systemd Configurado
- Arquivo: `/etc/systemd/system/postgres-mcp-sse.service`
- Status: Ativo e rodando
- Logs: `/var/log/postgres-mcp-sse.log`

### ⚠️ Nginx - Configuração Preparada
- Arquivo de configuração: `/root/.claude/postgres-mcp/nginx-postgres-sse.conf`
- Domínio: postgres-sse.agentesintegrados.com
- Requer: Nginx ou proxy reverso instalado

## Endpoints Disponíveis

### Local (já funcionando)
- Health: http://127.0.0.1:8000/health
- SSE: http://127.0.0.1:8000/sse
- Messages: http://127.0.0.1:8000/message

### Produção (após configurar proxy)
- Health: https://postgres-sse.agentesintegrados.com/health
- SSE: https://postgres-sse.agentesintegrados.com/sse
- Messages: https://postgres-sse.agentesintegrados.com/message

## Como Testar Localmente

1. **Verificar status do serviço:**
```bash
sudo systemctl status postgres-mcp-sse
```

2. **Testar endpoint de saúde:**
```bash
curl http://127.0.0.1:8000/health | jq
```

3. **Testar inicialização MCP:**
```bash
curl -X POST http://127.0.0.1:8000/message \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "initialize",
    "params": {
      "clientInfo": {
        "name": "test-client",
        "version": "1.0.0"
      }
    },
    "id": "1"
  }' | jq
```

4. **Listar ferramentas disponíveis:**
```bash
curl -X POST http://127.0.0.1:8000/message \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/list",
    "params": {},
    "id": "2"
  }' | jq
```

## Script de Teste Completo

Execute o script de teste incluído:
```bash
cd /root/.claude/postgres-mcp
source venv/bin/activate
python test_sse_server.py
```

## Configuração de Proxy Reverso

### Opção 1: Nginx
Se você tiver Nginx instalado, use a configuração em:
```
/root/.claude/postgres-mcp/nginx-postgres-sse.conf
```

### Opção 2: Caddy
```
postgres-sse.agentesintegrados.com {
    reverse_proxy /sse 127.0.0.1:8000 {
        flush_interval -1
    }
    reverse_proxy /message 127.0.0.1:8000
    reverse_proxy /health 127.0.0.1:8000
}
```

### Opção 3: Apache
```apache
<VirtualHost *:443>
    ServerName postgres-sse.agentesintegrados.com
    
    SSLEngine on
    SSLCertificateFile /path/to/cert.pem
    SSLCertificateKeyFile /path/to/key.pem
    
    ProxyPass /sse http://127.0.0.1:8000/sse
    ProxyPassReverse /sse http://127.0.0.1:8000/sse
    
    ProxyPass /message http://127.0.0.1:8000/message
    ProxyPassReverse /message http://127.0.0.1:8000/message
    
    ProxyPass /health http://127.0.0.1:8000/health
    ProxyPassReverse /health http://127.0.0.1:8000/health
    
    # SSE specific
    ProxyTimeout 86400
</VirtualHost>
```

## Logs e Monitoramento

### Logs do serviço
```bash
# Logs em tempo real
sudo journalctl -u postgres-mcp-sse -f

# Últimas 100 linhas
sudo journalctl -u postgres-mcp-sse -n 100

# Logs personalizados
tail -f /var/log/postgres-mcp-sse.log
tail -f /var/log/postgres-mcp-sse.error.log
```

### Monitoramento de saúde
```bash
# Script de monitoramento simples
while true; do
  curl -s http://127.0.0.1:8000/health | jq -r '.status'
  sleep 60
done
```

## Gerenciamento do Serviço

```bash
# Iniciar
sudo systemctl start postgres-mcp-sse

# Parar
sudo systemctl stop postgres-mcp-sse

# Reiniciar
sudo systemctl restart postgres-mcp-sse

# Habilitar início automático
sudo systemctl enable postgres-mcp-sse

# Desabilitar início automático
sudo systemctl disable postgres-mcp-sse

# Ver logs
sudo journalctl -u postgres-mcp-sse -f
```

## Variáveis de Ambiente

O serviço usa a seguinte variável de ambiente:
- `DATABASE_URI`: String de conexão PostgreSQL

Para alterar:
1. Edite `/etc/systemd/system/postgres-mcp-sse.service`
2. Modifique a linha `Environment="DATABASE_URI=..."`
3. Recarregue e reinicie:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl restart postgres-mcp-sse
   ```

## Integração com n8n

Para usar com n8n MCP Client:

1. **URL Base**: `https://postgres-sse.agentesintegrados.com` (após configurar proxy)
2. **Protocolo**: MCP sobre HTTP+SSE
3. **Autenticação**: Nenhuma (adicione se necessário)

### Exemplo de configuração n8n:
```json
{
  "serverUrl": "https://postgres-sse.agentesintegrados.com",
  "transport": "sse",
  "clientInfo": {
    "name": "n8n",
    "version": "1.0.0"
  }
}
```

## Troubleshooting

### Servidor não inicia
```bash
# Verificar logs
sudo journalctl -u postgres-mcp-sse -n 50

# Verificar se a porta está em uso
sudo lsof -i :8000

# Testar manualmente
cd /root/.claude/postgres-mcp
source venv/bin/activate
python -m src.postgres_mcp.server_sse --host 127.0.0.1 --port 8000
```

### Erro de conexão com banco
```bash
# Verificar conexão
psql $DATABASE_URI -c "SELECT 1"

# Verificar variável de ambiente
sudo systemctl show postgres-mcp-sse | grep Environment
```

### SSE não funciona
- Verificar timeouts do proxy
- Garantir que buffering está desabilitado
- Testar com curl:
  ```bash
  curl -N http://127.0.0.1:8000/sse
  ```

## Próximos Passos

1. **Configurar proxy reverso** (Nginx, Caddy, ou Apache)
2. **Configurar SSL/TLS** para o domínio
3. **Adicionar autenticação** se necessário
4. **Configurar monitoramento** (Prometheus, Grafana, etc.)
5. **Configurar backups** dos logs
6. **Testar com n8n** ou outro cliente MCP