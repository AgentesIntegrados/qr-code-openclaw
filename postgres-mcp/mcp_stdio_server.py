#!/usr/bin/env python3
"""MCP Server wrapper that keeps the process running"""
import asyncio
import sys
import os
import signal

# Add the source directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from postgres_mcp.server_simple import main

def signal_handler(sig, frame):
    print("Shutting down gracefully...")
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Run the main async function
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Interrupted")
        sys.exit(0)