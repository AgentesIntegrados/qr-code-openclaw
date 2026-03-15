# 🐳 Containerização do PostgreSQL MCP com Docker

## 🎯 Por que containerizar?

Containerizar o postgres-mcp oferece várias vantagens:

1. **Isolamento**: Dependências isoladas do sistema host
2. **Portabilidade**: Funciona em qualquer lugar que rode Docker
3. **Reprodutibilidade**: Ambiente consistente
4. **Facilidade**: Deploy com um único comando
5. **Segurança**: Isolamento de rede e filesystem

## 📋 Pré-requisitos

- Docker instalado
- Docker Compose (opcional)
- Acesso ao PostgreSQL (pode estar em outro container)

## 🏗️ Estrutura do Projeto

### 1. Dockerfile

```dockerfile
# /root/.claude/postgres-mcp/Dockerfile
FROM python:3.11-slim

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Criar diretório de trabalho
WORKDIR /app

# Copiar arquivos de requisitos
COPY requirements.txt .

# Instalar dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código fonte
COPY src/ ./src/
COPY handlers.py .
COPY start_postgres_mcp.sh .

# Tornar script executável
RUN chmod +x start_postgres_mcp.sh

# Variáveis de ambiente
ENV DATABASE_URI=""
ENV PYTHONUNBUFFERED=1

# Executar o MCP
CMD ["python", "src/postgres_mcp/server_simple.py"]
```

### 2. requirements.txt

```txt
# /root/.claude/postgres-mcp/requirements.txt
psycopg[binary]==3.1.19
mcp==1.1.2
```

### 3. docker-compose.yml

```yaml
# /root/.claude/postgres-mcp/docker-compose.yml
version: '3.8'

services:
  postgres-mcp:
    build: .
    container_name: postgres-mcp
    environment:
      - DATABASE_URI=${DATABASE_URI:-postgresql://user:pass@postgres:5432/db}
    networks:
      - mcp-network
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped
    stdin_open: true
    tty: true

  # Opcional: PostgreSQL local para testes
  postgres:
    image: postgres:15-alpine
    container_name: postgres-test
    environment:
      - POSTGRES_USER=test_user
      - POSTGRES_PASSWORD=test_pass
      - POSTGRES_DB=test_db
    volumes:
      - postgres-data:/var/lib/postgresql/data
    networks:
      - mcp-network
    ports:
      - "5432:5432"

networks:
  mcp-network:
    driver: bridge

volumes:
  postgres-data:
```

### 4. .dockerignore

```
# /root/.claude/postgres-mcp/.dockerignore
venv/
__pycache__/
*.pyc
*.pyo
*.pyd
.git/
.gitignore
*.md
backup_old/
docs/
tests/
.env.local
```

## 🚀 Como Usar

### Build da Imagem

```bash
cd /root/.claude/postgres-mcp
docker build -t postgres-mcp:latest .
```

### Executar com Docker

```bash
# Modo interativo (para MCP)
docker run -it --rm \
  -e DATABASE_URI="postgresql://evo_user:evo_pass@host.docker.internal:5432/evolution_db" \
  postgres-mcp:latest

# Ou conectando a um PostgreSQL em outro container
docker run -it --rm \
  --network evolution_network \
  -e DATABASE_URI="postgresql://evo_user:evo_pass@evolution_postgres:5432/evolution_db" \
  postgres-mcp:latest
```

### Executar com Docker Compose

```bash
# Criar arquivo .env
echo 'DATABASE_URI=postgresql://evo_user:evo_pass@host.docker.internal:5432/evolution_db' > .env

# Iniciar
docker-compose up -d

# Logs
docker-compose logs -f postgres-mcp

# Parar
docker-compose down
```

## 🔧 Integração com Claude Code

### Opção 1: Script Wrapper

```bash
#!/bin/bash
# /root/.claude/postgres-mcp/start-docker-mcp.sh

docker run -i --rm \
  -e DATABASE_URI="${DATABASE_URI}" \
  --network host \
  postgres-mcp:latest
```

```bash
# Adicionar ao Claude
claude mcp add postgres-mcp-docker -s user -- /root/.claude/postgres-mcp/start-docker-mcp.sh
```

### Opção 2: Docker Compose Exec

```bash
# Script para Claude
#!/bin/bash
docker-compose -f /root/.claude/postgres-mcp/docker-compose.yml exec -T postgres-mcp python src/postgres_mcp/server_simple.py
```

## 🛡️ Configurações de Segurança

### 1. Rede Isolada

```yaml
services:
  postgres-mcp:
    networks:
      - internal
    # Sem portas expostas

networks:
  internal:
    internal: true
```

### 2. Usuario Não-Root

```dockerfile
# Adicionar ao Dockerfile
RUN useradd -m -u 1000 mcp
USER mcp
```

### 3. Secrets Management

```yaml
# docker-compose com secrets
services:
  postgres-mcp:
    environment:
      - DATABASE_URI_FILE=/run/secrets/db_uri
    secrets:
      - db_uri

secrets:
  db_uri:
    file: ./secrets/database_uri.txt
```

## 🏃 Otimizações

### 1. Multi-stage Build

```dockerfile
# Build stage
FROM python:3.11-slim as builder
WORKDIR /build
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Runtime stage
FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .
ENV PATH=/root/.local/bin:$PATH
CMD ["python", "src/postgres_mcp/server_simple.py"]
```

### 2. Health Check

```dockerfile
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import psycopg; psycopg.connect('$DATABASE_URI')" || exit 1
```

### 3. Resource Limits

```yaml
services:
  postgres-mcp:
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 256M
        reservations:
          cpus: '0.1'
          memory: 128M
```

## 📊 Monitoramento

### Logs Estruturados

```python
# Adicionar ao server_simple.py
import logging
import json

logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    handlers=[logging.StreamHandler()]
)

def log_json(event, **kwargs):
    logging.info(json.dumps({
        "timestamp": datetime.utcnow().isoformat(),
        "event": event,
        **kwargs
    }))
```

### Métricas com Prometheus

```dockerfile
# Adicionar ao requirements.txt
prometheus-client==0.19.0

# Expor métricas
EXPOSE 8000
```

## 🚨 Troubleshooting

### Container não conecta ao PostgreSQL

```bash
# Verificar rede
docker network ls
docker network inspect bridge

# Usar host.docker.internal no Mac/Windows
# Usar IP real no Linux ou --network host
```

### MCP não responde

```bash
# Verificar logs
docker logs postgres-mcp

# Executar interativamente
docker run -it --entrypoint /bin/bash postgres-mcp:latest
```

### Performance issues

```bash
# Verificar recursos
docker stats postgres-mcp

# Aumentar limites
docker run -m 512m --cpus="1.0" postgres-mcp:latest
```

## 🎯 Benefícios Finais

1. **Deploy Simplificado**: `docker run` e pronto
2. **CI/CD Ready**: Fácil integração com pipelines
3. **Escalabilidade**: Múltiplas instâncias se necessário
4. **Versionamento**: Tags para diferentes versões
5. **Rollback Fácil**: Voltar versões anteriores

## 📦 Publicação

```bash
# Tag da imagem
docker tag postgres-mcp:latest seu-usuario/postgres-mcp:v2.0

# Push para registry
docker push seu-usuario/postgres-mcp:v2.0

# Ou GitHub Container Registry
docker tag postgres-mcp:latest ghcr.io/seu-usuario/postgres-mcp:v2.0
docker push ghcr.io/seu-usuario/postgres-mcp:v2.0
```

---

**PostgreSQL MCP containerizado** - Pronto para qualquer ambiente! 🐳