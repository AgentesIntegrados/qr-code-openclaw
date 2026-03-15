#!/usr/bin/env python3
"""Test the SSE server locally"""

import asyncio
import json
import aiohttp


async def test_health():
    """Test health endpoint"""
    async with aiohttp.ClientSession() as session:
        async with session.get('http://localhost:8002/health') as resp:
            print(f"Health check status: {resp.status}")
            data = await resp.json()
            print(json.dumps(data, indent=2))


async def test_sse_connection():
    """Test SSE connection"""
    async with aiohttp.ClientSession() as session:
        timeout = aiohttp.ClientTimeout(total=5)
        async with session.get('http://localhost:8002/sse', timeout=timeout) as resp:
            print(f"SSE connection status: {resp.status}")
            async for line in resp.content:
                if line:
                    print(f"SSE Event: {line.decode('utf-8').strip()}")
                    break  # Just test first event


async def test_message():
    """Test message endpoint"""
    async with aiohttp.ClientSession() as session:
        # Test initialize
        message = {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            },
            "id": "1"
        }
        
        async with session.post('http://localhost:8002/message', json=message) as resp:
            print(f"Initialize status: {resp.status}")
            data = await resp.json()
            print(json.dumps(data, indent=2))
        
        # Test tools/list
        message = {
            "jsonrpc": "2.0",
            "method": "tools/list",
            "params": {},
            "id": "2"
        }
        
        async with session.post('http://localhost:8002/message', json=message) as resp:
            print(f"\nTools list status: {resp.status}")
            data = await resp.json()
            print(f"Available tools: {len(data['result']['tools'])}")
            for tool in data['result']['tools'][:3]:  # Show first 3 tools
                print(f"  - {tool['name']}: {tool['description']}")


async def main():
    print("Testing PostgreSQL MCP SSE Server...")
    
    print("\n1. Testing health endpoint:")
    try:
        await test_health()
    except Exception as e:
        print(f"Health check failed: {e}")
    
    print("\n2. Testing SSE connection:")
    try:
        await test_sse_connection()
    except Exception as e:
        print(f"SSE connection failed: {e}")
    
    print("\n3. Testing message endpoint:")
    try:
        await test_message()
    except Exception as e:
        print(f"Message test failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())