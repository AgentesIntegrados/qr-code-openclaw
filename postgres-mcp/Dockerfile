FROM python:3.11-slim

# Metadados
LABEL maintainer="Diego (Claude)"
LABEL version="2.0"
LABEL description="PostgreSQL MCP Server with Performance Tools"

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Criar usuário não-root
RUN useradd -m -u 1000 mcp

# Criar diretório de trabalho
WORKDIR /app

# Copiar arquivos de requisitos primeiro (cache de camadas)
COPY requirements.txt .

# Instalar dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código fonte
COPY --chown=mcp:mcp src/ ./src/
COPY --chown=mcp:mcp handlers.py .
COPY --chown=mcp:mcp mcp_stdio_server.py .

# Criar diretório de logs
RUN mkdir -p /app/logs && chown mcp:mcp /app/logs

# Copiar e configurar entrypoint
COPY --chown=mcp:mcp docker_entrypoint.sh .
RUN chmod +x docker_entrypoint.sh

# Mudar para usuário não-root
USER mcp

# Variáveis de ambiente
ENV DATABASE_URI=""
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

# Executar o MCP
CMD ["./docker_entrypoint.sh"]