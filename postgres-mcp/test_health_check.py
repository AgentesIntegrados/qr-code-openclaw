import asyncio
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from handlers import PostgresHandlers

async def test():
    try:
        result = await PostgresHandlers.handle_health_check(None)
        print("Result:", result[0].text if result else "No result")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test())