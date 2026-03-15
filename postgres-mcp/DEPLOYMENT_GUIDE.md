# Guia de Implantação - PostgreSQL MCP

## 🏗️ Arquitetura Atual

### 1. Servidor MCP (Porta 8082)
- **Arquivo**: `mcp_simple_server.py`
- **URL**: http://localhost:8082/mcp
- **Protocolo**: MCP JSON-RPC 2.0
- **Uso**: Integração com n8n MCP Client

### 2. Servidor SSE/HTTP (Porta 8081) 
- **Arquivo**: `sse_server.py`
- **URL Externa**: https://postgres-sse.agentesintegrados.com
- **Protocolo**: REST API + SSE
- **Uso**: Acesso externo, dashboards, monitoramento

## 🚀 Como Iniciar

### Servidor MCP (para n8n):
```bash
cd /root/.claude/postgres-mcp
export DATABASE_URI="postgresql://user:pass@host:port/database"
python3 mcp_simple_server.py
```

### Servidor SSE (acesso externo):
```bash
cd /root/.claude/postgres-mcp
export DATABASE_URI="postgresql://user:pass@host:port/database"
export POSTGRES_SSE_TOKEN="seu_token_aqui"
python3 sse_server.py
```

## 🔧 Configuração como Serviço

### 1. Servidor MCP (systemd):
```bash
sudo tee /etc/systemd/system/postgres-mcp.service > /dev/null << 'EOF'
[Unit]
Description=PostgreSQL MCP Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/.claude/postgres-mcp
Environment="DATABASE_URI=postgresql://user:pass@localhost:port/database"
ExecStart=/usr/bin/python3 /root/.claude/postgres-mcp/mcp_simple_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable postgres-mcp
sudo systemctl start postgres-mcp
```

### 2. Servidor SSE (systemd):
```bash
sudo tee /etc/systemd/system/postgres-sse.service > /dev/null << 'EOF'
[Unit]
Description=PostgreSQL SSE Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/.claude/postgres-mcp
Environment="DATABASE_URI=postgresql://user:pass@localhost:port/database"
Environment="POSTGRES_SSE_TOKEN=EYjpWqb7YS1kJ0TKdJtVRN7Zj654NZbq6Ewe7RCHtPs"
ExecStart=/usr/bin/python3 /root/.claude/postgres-mcp/sse_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable postgres-sse
sudo systemctl start postgres-sse
```

## 📊 Monitoramento

### Verificar Status:
```bash
systemctl status postgres-mcp
systemctl status postgres-sse
```

### Ver Logs:
```bash
journalctl -u postgres-mcp -f
journalctl -u postgres-sse -f
```

### Testar Endpoints:
```bash
# MCP Server
curl http://localhost:8082/

# SSE Server (local)
curl -H "Authorization: Bearer TOKEN" http://localhost:8080/

# SSE Server (externo)
curl -H "Authorization: Bearer TOKEN" https://postgres-sse.agentesintegrados.com/
```

## 🛡️ Segurança

1. **Firewall**: Bloqueie acesso externo às portas 8081/8082
2. **Token**: Use tokens fortes em produção
3. **HTTPS**: Sempre use o domínio HTTPS para acesso externo
4. **Database**: Use credenciais seguras no DATABASE_URI

## 🔄 Atualizações

Para atualizar os servidores:
```bash
cd /root/.claude/postgres-mcp
git pull  # se estiver em git
systemctl restart postgres-mcp
systemctl restart postgres-sse
```