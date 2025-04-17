from fastapi import FastAPI, Depends, HTTPException, status, Response
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from database import get_db, Account, Transaction
from auth import get_current_user, User
from logging_config import logger, log_to_sentinel
from kafka_producer import produce_transaction_event
from encryption import encrypt_data, decrypt_data
from redis import Redis, ConnectionError
from prometheus_client import Counter, generate_latest
import uuid
import asyncio
import os

app = FastAPI(title="Banking Transaction API")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

# Initialize Redis with connection check
try:
    redis_client = Redis(host="redis", port=6379, decode_responses=True)
    redis_client.ping()
except ConnectionError as e:
    logger.error(f"Redis connection failed: {str(e)}")
    raise Exception("Failed to connect to Redis")

# Prometheus metrics
transactions_total = Counter("transactions_total", "Total transactions", ["type"])

class TransactionCreate(BaseModel):
    amount: float
    transaction_type: str  # deposit, withdrawal, transfer
    to_account_id: str | None = None

class TransactionResponse(BaseModel):
    id: str
    account_id: str
    amount: float
    transaction_type: str
    timestamp: str

@app.post("/accounts", response_model=dict)
async def create_account(user: User = Depends(get_current_user), db=Depends(get_db)):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    account_id = str(uuid.uuid4())
    encrypted_owner_id = encrypt_data(user.id)
    async with db as conn:
        await conn.execute("INSERT INTO accounts (id, balance, owner_id) VALUES ($1, $2, $3)", 
                         account_id, 0.0, encrypted_owner_id)
    await redis_client.set(f"account:{account_id}:balance", "0.0")
    logger.info("Account created", extra={"user_id": user.id, "account_id": account_id})
    log_to_sentinel({"event": "account_created", "account_id": account_id})
    return {"id": account_id, "balance": 0.0}

@app.post("/transactions", response_model=TransactionResponse)
async def create_transaction(
    transaction: TransactionCreate, 
    user: User = Depends(get_current_user), 
    db=Depends(get_db)
):
    if transaction.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    
    cache_key = f"account:{user.account_id}:balance"
    cached_balance = await redis_client.get(cache_key)
    
    async with db as conn:
        account = await conn.fetchrow("SELECT * FROM accounts WHERE id = $1", user.account_id)
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")
        decrypted_owner_id = decrypt_data(account["owner_id"])
        balance = float(cached_balance) if cached_balance else account["balance"]
        
        if transaction.transaction_type == "withdrawal" and balance < transaction.amount:
            logger.warning("Insufficient funds", extra={"account_id": user.account_id, "amount": transaction.amount})
            log_to_sentinel({"event": "insufficient_funds", "account_id": user.account_id})
            raise HTTPException(status_code=400, detail="Insufficient funds")
        
        if transaction.transaction_type == "transfer":
            to_account = await conn.fetchrow("SELECT * FROM accounts WHERE id = $1", transaction.to_account_id)
            if not to_account:
                raise HTTPException(status_code=404, detail="Recipient account not found")
            
            try:
                async with conn.transaction():
                    trans_id = str(uuid.uuid4())
                    await conn.execute(
                        "INSERT INTO transactions (id, account_id, amount, transaction_type, to_account_id) "
                        "VALUES ($1, $2, $3, $4, $5)",
                        trans_id, user.account_id, transaction.amount, transaction.transaction_type, transaction.to_account_id
                    )
                    await conn.execute(
                        "UPDATE accounts SET balance = balance - $1 WHERE id = $2",
                        transaction.amount, user.account_id
                    )
                    await conn.execute(
                        "UPDATE accounts SET balance = balance + $1 WHERE id = $2",
                        transaction.amount, transaction.to_account_id
                    )
                    new_balance = balance - transaction.amount
                    await redis_client.set(cache_key, str(new_balance))
                    await redis_client.set(f"account:{transaction.to_account_id}:balance", 
                                        str(to_account["balance"] + transaction.amount))
            except Exception as e:
                logger.error(f"Transfer failed: {str(e)}", extra={"account_id": user.account_id})
                log_to_sentinel({"event": "transfer_failed", "account_id": user.account_id})
                raise HTTPException(status_code=500, detail="Transaction failed")
        
        else:
            trans_id = str(uuid.uuid4())
            await conn.execute(
                "INSERT INTO transactions (id, account_id, amount, transaction_type) "
                "VALUES ($1, $2, $3, $4)",
                trans_id, user.account_id, transaction.amount, transaction.transaction_type
            )
            if transaction.transaction_type == "deposit":
                new_balance = balance + transaction.amount
                await conn.execute("UPDATE accounts SET balance = balance + $1 WHERE id = $2", 
                                 transaction.amount, user.account_id)
            else:
                new_balance = balance - transaction.amount
                await conn.execute("UPDATE accounts SET balance = balance - $1 WHERE id = $2", 
                                 transaction.amount, user.account_id)
            await redis_client.set(cache_key, str(new_balance))
        
        await produce_transaction_event({
            "id": trans_id,
            "account_id": user.account_id,
            "amount": transaction.amount,
            "type": transaction.transaction_type
        })
        
        transactions_total.labels(type=transaction.transaction_type).inc()
        
        logger.info("Transaction processed", extra={
            "account_id": user.account_id, 
            "type": transaction.transaction_type, 
            "amount": transaction.amount
        })
        log_to_sentinel({"event": "transaction_processed", "transaction_id": trans_id})
        return TransactionResponse(
            id=trans_id,
            account_id=user.account_id,
            amount=transaction.amount,
            transaction_type=transaction.transaction_type,
            timestamp=str((await conn.fetchrow("SELECT timestamp FROM transactions WHERE id = $1", trans_id))["timestamp"])
        )

@app.get("/transactions", response_model=list[TransactionResponse])
async def get_transactions(user: User = Depends(get_current_user), db=Depends(get_db)):
    async with db as conn:
        transactions = await conn.fetch("SELECT * FROM transactions WHERE account_id = $1", user.account_id)
    logger.info("Fetched transactions", extra={"account_id": user.account_id, "count": len(transactions)})
    log_to_sentinel({"event": "transactions_fetched", "account_id": user.account_id})
    return [TransactionResponse(
        id=t["id"],
        account_id=t["account_id"],
        amount=t["amount"],
        transaction_type=t["transaction_type"],
        timestamp=str(t["timestamp"])
    ) for t in transactions]

@app.get("/metrics")
async def metrics():
    return Response(content=generate_latest(), media_type="text/plain")