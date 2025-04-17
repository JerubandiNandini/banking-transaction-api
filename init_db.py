import sys
import os
from pathlib import Path

# Add the /app directory to the Python path
sys.path.append(str(Path(__file__).parent))

from database import init_db
import asyncio

if __name__ == "__main__":
    asyncio.run(init_db())
    print("Database initialized successfully")