import asyncpg
from contextlib import asynccontextmanager
from logging_config import logger

DATABASE_URL = "postgresql://user:password@postgres:5432/banking_db"

async def init_db():
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                id TEXT PRIMARY KEY,
                balance FLOAT NOT NULL,
                owner_id TEXT NOT NULL,
                INDEX idx_account_id (id)
            ) PARTITION BY RANGE (balance);
            CREATE TABLE IF NOT EXISTS accounts_low PARTITION OF accounts FOR VALUES FROM (0) TO (10000);
            CREATE TABLE IF NOT EXISTS accounts_high PARTITION OF accounts FOR VALUES FROM (10000) TO (MAXVALUE);
            
            CREATE TABLE IF NOT EXISTS transactions (
                id TEXT PRIMARY KEY,
                account_id TEXT NOT NULL,
                amount FLOAT NOT NULL,
                transaction_type TEXT NOT NULL,
                to_account_id TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_account_id_timestamp (account_id, timestamp)
            );
        """)
        await conn.close()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        raise

@asynccontextmanager
async def get_db():
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        yield conn
    except asyncpg.exceptions.PostgresError as e:
        logger.error(f"Database connection failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Database connection error")
    finally:
        await conn.close()