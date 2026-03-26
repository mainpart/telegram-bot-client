import logging
from adapters.base import BaseAdapter

logger = logging.getLogger(__name__)

class MongoDBAdapter(BaseAdapter):
    def __init__(self, config: dict):
        from motor.motor_asyncio import AsyncIOMotorClient
        self._motor_client_class = AsyncIOMotorClient
        self.uri = config.get('uri')
        self.database_name = config.get('database') or config.get('db')
        self.collection_name = config.get('collection') or 'messages'
        self._client = None
        self._collection = None

    async def init(self):
        if not self.uri or not self.database_name:
            logger.error("MongoDBAdapter requires 'uri' and 'database'")
            return
        self._client = self._motor_client_class(self.uri)
        db = self._client[self.database_name]
        self._collection = db[self.collection_name]

    async def exec(self, message: dict):
        if not self._collection:
            await self.init()
            if not self._collection:
                return
        try:
            await self._collection.insert_one(message)
        except Exception as e:
            logger.error(f"MongoDBAdapter error: {e}")

    async def close(self):
        try:
            if self._client:
                self._client.close()
        except Exception as e:
            logger.error(f"MongoDBAdapter close error: {e}")
