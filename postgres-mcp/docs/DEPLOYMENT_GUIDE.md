# 🚀 Guia de Deployment - PostgreSQL MCP v2.0

## 📋 Checklist de Pré-Deployment

### Ambiente Local
- [ ] Python 3.11+ instalado
- [ ] PostgreSQL acessível
- [ ] Variável DATABASE_URI configurada
- [ ] Permissões de leitura no banco

### Ambiente Docker
- [ ] Docker instalado e rodando
- [ ] docker-compose instalado (opcional)
- [ ] Rede configurada para acessar PostgreSQL

## 🏗️ Opções de Deployment

### 1. Deployment Local (Desenvolvimento)

```bash
# Clone ou copie os arquivos
cd /root/.claude/postgres-mcp

# Ative o ambiente virtual
source venv/bin/activate

# Configure a conexão
export DATABASE_URI="postgresql://user:pass@localhost:5432/db"

# Teste manual
python src/postgres_mcp/server_simple.py

# Adicione ao Claude Code
claude mcp add postgres-mcp -s user -- /root/.claude/postgres-mcp/start_postgres_mcp.sh
```

### 2. Deployment Docker (Produção)

```bash
# Build da imagem
cd /root/.claude/postgres-mcp
docker build -t postgres-mcp:latest .

# Teste a imagem
docker run -it --rm \
  -e DATABASE_URI="$DATABASE_URI" \
  postgres-mcp:latest

# Deploy com docker-compose
docker-compose up -d

# Adicione ao Claude Code
claude mcp add postgres-mcp-docker -s user -- /root/.claude/postgres-mcp/start-docker-mcp.sh
```

### 3. Deployment em Kubernetes

```yaml
# postgres-mcp-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: postgres-mcp
spec:
  replicas: 1
  selector:
    matchLabels:
      app: postgres-mcp
  template:
    metadata:
      labels:
        app: postgres-mcp
    spec:
      containers:
      - name: postgres-mcp
        image: postgres-mcp:latest
        env:
        - name: DATABASE_URI
          valueFrom:
            secretKeyRef:
              name: postgres-secret
              key: connection-string
        resources:
          limits:
            memory: "256Mi"
            cpu: "500m"
          requests:
            memory: "128Mi"
            cpu: "100m"
```

## 🔒 Segurança em Produção

### 1. Gerenciamento de Credenciais

```bash
# Nunca commite credenciais!
echo "DATABASE_URI=..." >> .env
echo ".env" >> .gitignore

# Use secrets do Docker
docker secret create db_uri ./database_uri.txt
```

### 2. Permissões Mínimas

```sql
-- Crie um usuário read-only para o MCP
CREATE USER mcp_reader WITH PASSWORD 'secure_password';
GRANT CONNECT ON DATABASE your_db TO mcp_reader;
GRANT USAGE ON SCHEMA public TO mcp_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO mcp_reader;
GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO mcp_reader;

-- Para pg_stat_statements
GRANT pg_read_all_stats TO mcp_reader;
```

### 3. Network Security

```yaml
# docker-compose com rede isolada
services:
  postgres-mcp:
    networks:
      - internal
    # Sem portas expostas!

networks:
  internal:
    internal: true
```

## 📊 Monitoramento e Logs

### 1. Configurar Logs Estruturados

```python
# Adicionar ao server_simple.py
import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_obj = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'message': record.getMessage(),
            'tool': getattr(record, 'tool', 'unknown')
        }
        return json.dumps(log_obj)

# Configure logging
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logging.basicConfig(level=logging.INFO, handlers=[handler])
```

### 2. Métricas com Prometheus

```python
# Adicionar métricas
from prometheus_client import Counter, Histogram, start_http_server

# Métricas
query_counter = Counter('postgres_mcp_queries_total', 'Total queries executed', ['tool'])
query_duration = Histogram('postgres_mcp_query_duration_seconds', 'Query duration', ['tool'])

# Iniciar servidor de métricas
start_http_server(8000)
```

### 3. Health Endpoint

```python
# Adicionar health check HTTP
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'{"status": "healthy"}')

# Rodar em thread separada
health_server = HTTPServer(('0.0.0.0', 8080), HealthHandler)
threading.Thread(target=health_server.serve_forever, daemon=True).start()
```

## 🔄 CI/CD Pipeline

### GitHub Actions

```yaml
# .github/workflows/postgres-mcp.yml
name: PostgreSQL MCP CI/CD

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-asyncio
    
    - name: Run tests
      run: pytest tests/
    
  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Build Docker image
      run: docker build -t postgres-mcp:${{ github.sha }} .
    
    - name: Push to registry
      run: |
        echo ${{ secrets.DOCKER_PASSWORD }} | docker login -u ${{ secrets.DOCKER_USERNAME }} --password-stdin
        docker push postgres-mcp:${{ github.sha }}
```

## 🔧 Troubleshooting em Produção

### 1. Debug Remoto

```bash
# Conectar ao container em execução
docker exec -it postgres-mcp /bin/bash

# Ver logs
docker logs -f postgres-mcp --tail 100

# Testar conexão do container
docker exec postgres-mcp python -c "import psycopg; print(psycopg.connect('$DATABASE_URI'))"
```

### 2. Performance Issues

```bash
# Verificar uso de recursos
docker stats postgres-mcp

# Aumentar limites se necessário
docker update --memory="512m" --cpus="1" postgres-mcp
```

### 3. Connection Issues

```bash
# Testar conectividade de rede
docker exec postgres-mcp ping postgres-host

# Verificar DNS
docker exec postgres-mcp nslookup postgres-host

# Testar porta
docker exec postgres-mcp nc -zv postgres-host 5432
```

## 📈 Scaling

### Horizontal Scaling

```yaml
# docker-compose com replicas
services:
  postgres-mcp:
    image: postgres-mcp:latest
    deploy:
      replicas: 3
      restart_policy:
        condition: on-failure
```

### Load Balancing

```nginx
# nginx.conf para múltiplas instâncias
upstream postgres_mcp {
    least_conn;
    server mcp1:80;
    server mcp2:80;
    server mcp3:80;
}
```

## 🎯 Best Practices

### 1. Versionamento

```bash
# Tag semântico
git tag -a v2.0.0 -m "Release v2.0.0"
docker tag postgres-mcp:latest postgres-mcp:v2.0.0
```

### 2. Backup de Configurações

```bash
# Backup de configs
tar -czf postgres-mcp-config-$(date +%Y%m%d).tar.gz \
  .env \
  docker-compose.yml \
  start-docker-mcp.sh
```

### 3. Documentação de Incidentes

```markdown
# incident-template.md
## Incidente: [TITULO]
- **Data**: YYYY-MM-DD HH:MM
- **Severidade**: Alta/Média/Baixa
- **Descrição**: O que aconteceu
- **Causa Raiz**: Por que aconteceu
- **Resolução**: Como foi resolvido
- **Prevenção**: Como evitar no futuro
```

## 🌍 Deployment Multi-Ambiente

### Desenvolvimento

```bash
export MCP_ENV=development
export DATABASE_URI="postgresql://dev_user:dev_pass@localhost:5432/dev_db"
```

### Staging

```bash
export MCP_ENV=staging
export DATABASE_URI="postgresql://stage_user:stage_pass@stage-db:5432/stage_db"
```

### Produção

```bash
export MCP_ENV=production
export DATABASE_URI="postgresql://prod_user:${PROD_PASS}@prod-db:5432/prod_db"
```

## 📝 Checklist Final

- [ ] Imagem Docker construída e testada
- [ ] Credenciais seguras configuradas
- [ ] Logs configurados e funcionando
- [ ] Monitoramento ativo
- [ ] Documentação atualizada
- [ ] Backup de configurações
- [ ] Plano de rollback definido
- [ ] Equipe treinada

## 🎉 Conclusão

Com este guia, o PostgreSQL MCP v2.0 está pronto para ser deployado em qualquer ambiente, desde desenvolvimento local até produção em escala.

Lembre-se: **Segurança primeiro, performance segundo, features terceiro!**

---

*Deployment Guide v1.0*
*PostgreSQL MCP v2.0 Ready for Production* 🚀