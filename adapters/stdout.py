import json
import logging
from adapters.base import BaseAdapter

logger = logging.getLogger(__name__)

class StdoutAdapter(BaseAdapter):
    def __init__(self, config: dict):
        self.pretty = bool(config.get('pretty', True))

    async def exec(self, message: dict):
        try:
            if self.pretty:
                print(json.dumps(message, indent=2, ensure_ascii=False))
            else:
                print(json.dumps(message, ensure_ascii=False))
        except Exception as e:
            logger.error(f"StdoutAdapter error: {e}")
