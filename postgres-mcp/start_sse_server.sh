#!/bin/bash
# Script to start PostgreSQL MCP SSE Server

# Load environment variables if .env exists
if [ -f "$(dirname "$0")/.env" ]; then
    export $(cat "$(dirname "$0")/.env" | grep -v '^#' | xargs)
fi

# Ensure DATABASE_URI is set
if [ -z "$DATABASE_URI" ]; then
    echo "DATABASE_URI environment variable not set. Using default."
    export DATABASE_URI="postgresql://evo_user:evo_pass@localhost:5432/evolution_db"
fi

# Change to script directory
cd "$(dirname "$0")"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Install/update dependencies
pip install -r requirements.txt

# Start the SSE server
echo "Starting PostgreSQL MCP SSE Server..."
echo "DATABASE_URI: ${DATABASE_URI}"
python -m src.postgres_mcp.server_sse --host 0.0.0.0 --port 8000