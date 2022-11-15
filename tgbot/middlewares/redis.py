from aiogram.dispatcher.middlewares import LifetimeControllerMiddleware
from aioredis import Redis, ConnectionPool

class RedisMiddleware(LifetimeControllerMiddleware):
    skip_patterns = ['error', 'update']

    def __init__(self, connection_pool: ConnectionPool):
        super().__init__()
        self.connection_pool = connection_pool

    async def pre_process(self, obj, data, *args):
        redis = Redis(connection_pool=self.connection_pool)
        data['redis'] = redis

    async def post_process(self, obj, data, *args):
        redis: Redis = data['redis']
        await redis.close()