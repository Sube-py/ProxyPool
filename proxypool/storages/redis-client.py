import asyncio
from typing import List, Tuple
from random import choice
from loguru import logger
from redis.asyncio import StrictRedis
from proxypool.exceptions import PoolEmptyException
from proxypool.config import config
from proxypool.schemas.proxy import ProxySchema


class RedisClient(object):
    """
    Redis connection client of proxypool.
    """
    def __init__(
        self,
        host: str = config.redis.host,
        port: int = config.redis.port,
        password: str = config.redis.password,
        db: int = config.redis.db,
        connection_string: str = config.redis.connection_string,
        **kwargs,
    ):
        """
        :param host: redis host
        :param port: redis port
        :param password: redis password
        :param db: redis db
        :param connection_string: redis connection string
        """
        # if set connection_string, just use it
        if connection_string:
            self.db = StrictRedis.from_url(connection_string, decode_responses=True, **kwargs)
        else:
            self.db = StrictRedis(host=host, port=port, password=password, db=db, decode_responses=True, **kwargs)

    async def add(self, proxy: ProxySchema, score: int = config.score.init) -> int:
        """
        Add proxy to redis.
        :param proxy: ProxySchema
        :param score: score of proxy
        :return: int
        """
        if not proxy.is_valid_proxy(f'{proxy.host}:{proxy.port}'):
            logger.info(f'Invalid proxy: {proxy}, throw it.')
            return -1
        if not await self.exists(proxy):
            return await self.db.zadd(config.redis.proxy_key, {proxy.string(): score})

    async def random(self) -> ProxySchema:
        """
        Get random proxy
        firstly try to get proxy with max score
        if not exists, try to get proxy by rank
        if not exists, raise error
        :return: ProxySchema
        """
        # try to get proxy with max score
        proxies = await self.db.zrangebyscore(
            config.redis.proxy_key,
            config.score.max,
            config.score.max,
        )
        if len(proxies):
            return ProxySchema.convert_proxy_or_proxies(choice(proxies))
        # else get proxy by rank
        proxies = await self.db.zrangebyscore(
            config.redis.proxy_key,
            config.score.min,
            config.score.max,
        )
        if len(proxies):
            return ProxySchema.convert_proxy_or_proxies(choice(proxies))
        # else raise error
        raise PoolEmptyException

    async def decrease(self, proxy: ProxySchema):
        """
        Decrease score of proxy
        if smaller than score min, delete proxy
        :param proxy: ProxySchema
        :return: int
        """
        score = await self.db.zincrby(config.redis.proxy_key, -1, proxy.string())
        logger.info(f'{proxy.string()} score decrease 1, current {score}')
        if score <= config.score.min:
            logger.info(f'{proxy.string()} is invalid, delete it.')
            await self.db.zrem(config.redis.proxy_key, proxy.string())

    async def exists(self, proxy: ProxySchema) -> bool:
        """
        Check proxy exists in redis
        :param proxy: ProxySchema
        :return: bool
        """
        return not await self.db.zscore(config.redis.proxy_key, proxy.string()) is None

    async def max(self, proxy: ProxySchema) -> int:
        """
        Set max score to max score
        :param proxy: ProxySchema
        :return: int
        """
        logger.info(f'{proxy.string()} is valid, set to {config.score.max}')
        await self.db.zadd(config.redis.proxy_key, {proxy.string(): config.score.max})
        return int(await self.db.zscore(config.redis.proxy_key, proxy.string()))

    async def count(self) -> int:
        """
        Count proxies in redis
        :return: int
        """
        return await self.db.zcard(config.redis.proxy_key)

    async def all(self) -> List[ProxySchema]:
        """
        Get all proxies in redis
        :return: List[ProxySchema]
        """
        proxies = await self.db.zrangebyscore(config.redis.proxy_key, config.score.min, config.score.max)
        return ProxySchema.convert_proxy_or_proxies(proxies)

    async def batch(self, cursor: int, count: int) -> Tuple[int, List[ProxySchema]]:
        """
        Get batch proxies in redis
        :param cursor: int
        :param count: int
        :return: List[ProxySchema]
        """
        cursor, proxies = await self.db.zscan(config.redis.proxy_key, cursor, count=count)
        return cursor, ProxySchema.convert_proxy_or_proxies([data[0] for data in proxies])


if __name__ == '__main__':
    async def test_redis():
        client = RedisClient()
        # await client.add(ProxySchema(host='127.0.0.1', port='7891'))
        # p = await client.random()
        p = await client.batch(50, 10)
        print(p)
    asyncio.get_event_loop().run_until_complete(test_redis())
