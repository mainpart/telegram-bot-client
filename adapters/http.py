import asyncio
import logging
import aiohttp
from adapters.base import BaseAdapter

logger = logging.getLogger(__name__)

class HttpAdapter(BaseAdapter):
    def __init__(self, config: dict):
        self.url = config.get('url')
        self.method = (config.get('method') or 'POST').upper()
        self.headers = config.get('headers') or {}
        self.timeout_seconds = int(config.get('timeout', 10))
        self._session = None

    async def init(self):
        timeout = aiohttp.ClientTimeout(total=self.timeout_seconds)
        self._session = aiohttp.ClientSession(timeout=timeout)

    async def exec(self, message: dict):
        if not self.url:
            logger.error("HttpAdapter: 'url' is required")
            return
        if not self._session:
            await self.init()
        try:
            async with self._session.request(self.method, self.url, json=message, headers=self.headers) as resp:
                await resp.read()
                if resp.status >= 400:
                    logger.error(f"HttpAdapter failed with status {resp.status}")
        except asyncio.TimeoutError as e:
            logger.error(f"HttpAdapter timeout error: {e}")
        except aiohttp.ClientConnectionError as e:
            logger.error(f"HttpAdapter connection error: {e}")
        except aiohttp.ServerDisconnectedError as e:
            logger.error(f"HttpAdapter server disconnected: {e}")
        except aiohttp.ClientConnectorError as e:
            logger.error(f"HttpAdapter connector error: {e}")
        except Exception as e:
            logger.error(f"HttpAdapter error: {e}")

    async def close(self):
        if self._session:
            try:
                await self._session.close()
            except Exception as e:
                logger.error(f"HttpAdapter close error: {e}")
            finally:
                self._session = None
