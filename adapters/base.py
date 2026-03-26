class BaseAdapter:
    async def init(self):
        return

    async def exec(self, message: dict):
        raise NotImplementedError
