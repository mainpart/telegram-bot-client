import json
import logging
from adapters.base import BaseAdapter

logger = logging.getLogger(__name__)

class RabbitMQAdapter(BaseAdapter):
    def __init__(self, config: dict):
        self.url = config.get('url') or 'amqp://guest:guest@localhost/'
        self.exchange = config.get('exchange') or ''
        self.routing_key = config.get('routing_key') or 'telegram'
        self._connection = None
        self._channel = None

    async def init(self):
        import aio_pika
        self._connection = await aio_pika.connect_robust(self.url)
        self._channel = await self._connection.channel()

    async def exec(self, message: dict):
        if not self._channel:
            await self.init()
        import aio_pika
        body = json.dumps(message, ensure_ascii=False).encode()
        await self._channel.default_exchange.publish(
            aio_pika.Message(body=body, content_type='application/json'),
            routing_key=self.routing_key,
        )

    async def close(self):
        try:
            if self._connection:
                await self._connection.close()
        except Exception as e:
            logger.error(f"RabbitMQAdapter close error: {e}")
