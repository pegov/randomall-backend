import asyncio
from typing import List, Optional

from aioredis import Redis


class RedisCache:
    def __init__(self, conn: Redis) -> None:
        self.conn = conn
        self.background_tasks: List[asyncio.Task] = []

    def background(self, fut) -> None:
        task = asyncio.create_task(fut)
        self.background_tasks.append(task)

    async def get(self, key: str) -> Optional[str]:
        return await self.conn.get(key)

    async def mget(self, keys: List[str]) -> List[Optional[str]]:
        return await self.conn.mget(keys)

    async def delete(self, key: str) -> None:
        await self.conn.delete(key)

    async def keys(self, match: str) -> List[str]:
        return await self.conn.keys(match)

    async def set(self, key: str, value: str | int | bytes, ex: int) -> None:
        await self.conn.set(key, value, ex=ex)

    async def setnx(self, key: str, value: str | int | bytes, ex: int) -> None:
        await self.conn.set(key, value, ex=ex, nx=True)

    async def incr(self, key: str) -> int:
        return int(await self.conn.incr(key))

    async def decr(self, key: str) -> int:
        return int(await self.conn.decr(key))

    async def ttl(self, key: str) -> int:
        """
        -2 - not set
        -1 - no expire
        >0 - expire
        """
        return await self.conn.ttl(key)

    async def sadd_single(self, key: str, value: int) -> None:
        await self.conn.sadd(key, value)

    async def sadd_multiple(self, key: str, values: List[int]) -> None:
        if len(values) > 0:
            await self.conn.sadd(key, *values)

    async def smembers(self, key: str) -> List[str]:
        return await self.conn.smembers(key)

    async def sismember(self, key: str, value) -> bool:
        return bool(await self.conn.sismember(key, value))

    async def srem(self, key: str, value):
        await self.conn.srem(key, value)
