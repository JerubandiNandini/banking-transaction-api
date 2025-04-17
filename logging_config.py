import logging
from logstash_async.handler import AsynchronousLogstashHandler
import aiohttp
import os

logger = logging.getLogger("banking-api")
logger.setLevel(logging.INFO)

logstash_handler = AsynchronousLogstashHandler(
    host="logstash",
    port=5044,
    database_path=None
)
logger.addHandler(logstash_handler)

async def log_to_sentinel(event):
    sentinel_endpoint = os.getenv("SENTINEL_ENDPOINT", "https://mock-sentinel-api.azure.com/log")
    headers = {"Authorization": f"Bearer {os.getenv('SENTINEL_TOKEN', 'mock-token')}"}
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(sentinel_endpoint, json=event, headers=headers) as response:
                if response.status == 200:
                    logger.info("Sent to Sentinel", extra=event)
                else:
                    logger.error(f"Sentinel API call failed: {response.status}", extra=event)
        except Exception as e:
            logger.error(f"Sentinel API error: {str(e)}", extra=event)