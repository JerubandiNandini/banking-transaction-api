from aiokafka import AIOKafkaProducer
from logging_config import logger
import json

async def produce_transaction_event(event: dict):
    try:
        producer = AIOKafkaProducer(bootstrap_servers="kafka:9092")
        await producer.start()
        await producer.send_and_wait("transactions", json.dumps(event).encode("utf-8"))
        logger.info("Published transaction event to Kafka", extra=event)
    except Exception as e:
        logger.error(f"Kafka producer error: {str(e)}", extra=event)
        raise
    finally:
        await producer.stop()