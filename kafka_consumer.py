from aiokafka import AIOKafkaConsumer
from logging_config import logger, log_to_sentinel
import json
import asyncio

async def consume_transactions():
    try:
        consumer = AIOKafkaConsumer(
            "transactions",
            bootstrap_servers="kafka:9092",
            group_id="banking-consumer-group"
        )
        await consumer.start()
        async for msg in consumer:
            event = json.loads(msg.value.decode("utf-8"))
            logger.info("Consumed transaction event", extra=event)
            await log_to_sentinel({"event": "transaction_consumed", "transaction_id": event["id"]})
            if event["amount"] > 10000:
                await log_to_sentinel({"event": "suspicious_transaction", "transaction_id": event["id"], "amount": event["amount"]})
    except Exception as e:
        logger.error(f"Kafka consumer error: {str(e)}")
    finally:
        await consumer.stop()

if __name__ == "__main__":
    asyncio.run(consume_transactions())