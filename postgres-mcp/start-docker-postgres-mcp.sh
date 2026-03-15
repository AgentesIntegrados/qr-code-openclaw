#!/bin/bash
# Start script for postgres-mcp in Docker mode

# Check if container is already running
if docker ps --format '{{.Names}}' | grep -q '^postgres-mcp$'; then
    echo "postgres-mcp container is already running"
else
    echo "Starting postgres-mcp container..."
    docker start postgres-mcp 2>/dev/null || {
        echo "Container not found, creating new one..."
        docker run -d --name postgres-mcp \
            --env-file /root/.claude/postgres-mcp/.env \
            --restart unless-stopped \
            postgres-mcp:latest
    }
fi

# Connect to the container's stdio
docker attach postgres-mcp