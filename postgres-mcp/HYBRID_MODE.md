# PostgreSQL MCP - Modo Híbrido

O postgres-mcp agora suporta modo híbrido com MCP (stdio) e SSE/HTTP endpoints.

## 🚀 Componentes

### 1. MCP Server (stdio)
- **Arquivo**: `src/postgres_mcp/server_simple.py`
- **Uso**: Comunicação com Claude Code via protocolo MCP
- **Inicialização**: `claude mcp add postgres-mcp -s user -- /root/.claude/postgres-mcp/start_postgres_mcp.sh`

### 2. SSE/HTTP Server
- **Arquivo**: `sse_server.py`
- **Porta**: 8081
- **URL Externa**: https://postgres-sse.agentesintegrados.com
- **Autenticação**: Bearer Token obrigatório

## 🔐 Autenticação

### Gerar Token
```bash
cd /root/.claude/postgres-mcp
python3 generate_token.py
```

### Token Atual
```bash
export POSTGRES_SSE_TOKEN='EYjpWqb7YS1kJ0TKdJtVRN7Zj654NZbq6Ewe7RCHtPs'
```

## 📡 Endpoints Disponíveis

### SSE (Server-Sent Events)
- `GET /sse/test-connection` - Monitora conexão em tempo real
- `GET /sse/health-check` - Monitora saúde do banco
- `GET /sse/monitor-queries` - Monitora queries ativas
- `GET /sse/monitor-locks` - Monitora bloqueios

### HTTP API
- `POST /api/test-connection` - Testa conexão
- `GET /api/list-schemas` - Lista schemas
- `GET /api/list-tables?schema=public` - Lista tabelas
- `POST /api/execute-query` - Executa query
- `POST /api/explain-query` - Analisa plano
- `GET /api/slow-queries` - Queries lentas
- `GET /api/health-check` - Verificação de saúde
- `GET /api/suggest-indexes` - Sugestões de índices
- `GET /api/table-stats` - Estatísticas de tabelas
- `GET /api/index-usage` - Análise de índices
- `GET /api/blocking-queries` - Queries bloqueadas

## 🌐 Acesso Externo

### URL: https://postgres-sse.agentesintegrados.com

### Exemplo JavaScript (SSE):
```javascript
const token = 'EYjpWqb7YS1kJ0TKdJtVRN7Zj654NZbq6Ewe7RCHtPs';
const eventSource = new EventSource('https://postgres-sse.agentesintegrados.com/sse/health-check', {
    headers: {
        'Authorization': `Bearer ${token}`
    }
});

eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('Health update:', data);
};
```

### Exemplo cURL (API):
```bash
curl -H "Authorization: Bearer EYjpWqb7YS1kJ0TKdJtVRN7Zj654NZbq6Ewe7RCHtPs" \
     https://postgres-sse.agentesintegrados.com/api/list-schemas
```

### Exemplo Python:
```python
import requests
import sseclient

# API Request
headers = {'Authorization': 'Bearer EYjpWqb7YS1kJ0TKdJtVRN7Zj654NZbq6Ewe7RCHtPs'}
response = requests.get('https://postgres-sse.agentesintegrados.com/api/health-check', headers=headers)
print(response.json())

# SSE Stream
response = requests.get('https://postgres-sse.agentesintegrados.com/sse/monitor-queries', 
                       headers=headers, stream=True)
client = sseclient.SSEClient(response)
for event in client.events():
    print(event.data)
```

## 🚀 Inicialização

### 1. Iniciar servidor SSE (manualmente):
```bash
cd /root/.claude/postgres-mcp
export DATABASE_URI="postgresql://evo_user:evo_pass@localhost:5432/evolution_db"
export POSTGRES_SSE_TOKEN='EYjpWqb7YS1kJ0TKdJtVRN7Zj654NZbq6Ewe7RCHtPs'
python3 sse_server.py
```

### 2. Iniciar como serviço (recomendado):
```bash
# Criar serviço systemd
sudo tee /etc/systemd/system/postgres-sse.service > /dev/null << EOF
[Unit]
Description=PostgreSQL SSE Server
After=network.target postgresql.service

[Service]
Type=simple
User=root
WorkingDirectory=/root/.claude/postgres-mcp
Environment="DATABASE_URI=postgresql://evo_user:evo_pass@localhost:5432/evolution_db"
Environment="POSTGRES_SSE_TOKEN=EYjpWqb7YS1kJ0TKdJtVRN7Zj654NZbq6Ewe7RCHtPs"
ExecStart=/usr/bin/python3 /root/.claude/postgres-mcp/sse_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Habilitar e iniciar
sudo systemctl daemon-reload
sudo systemctl enable postgres-sse
sudo systemctl start postgres-sse
```

## 📊 Monitoramento

### Verificar status:
```bash
systemctl status postgres-sse
```

### Ver logs:
```bash
journalctl -u postgres-sse -f
```

### Logs do Caddy:
```bash
tail -f /etc/caddy/logs/postgres-sse.log
```

## 🔧 Configuração de Bancos

### Bancos disponíveis:
```bash
# Evolution API Principal (porta 5432)
export DATABASE_URI="postgresql://evo_user:evo_pass@localhost:5432/evolution_db"

# Alexandre (porta 5433)
export DATABASE_URI="postgresql://evo_user:evo_pass@localhost:5433/evolution_db"

# V4Company (porta 5434)
export DATABASE_URI="postgresql://evo_user:evo_pass@localhost:5434/evolution_db"

# G4Educacao (porta 5435)
export DATABASE_URI="postgresql://evo_user:evo_pass@localhost:5435/evolution_db"
```

## 🛡️ Segurança

1. **Token Bearer**: Sempre use autenticação em produção
2. **HTTPS**: Caddy fornece SSL automático
3. **CORS**: Configurado para permitir qualquer origem (ajuste conforme necessário)
4. **Rate Limiting**: Considere adicionar no Caddy se necessário

## 📝 Notas

- O servidor MCP continua funcionando normalmente via stdio
- O servidor SSE é independente e pode ser parado sem afetar o MCP
- Ambos compartilham os mesmos handlers (`handlers.py`)
- A configuração do banco é via variável DATABASE_URI