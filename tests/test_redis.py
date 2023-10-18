from typing import Iterable
import pytest

from aioredis import Redis

from app.db.redis import RedisCache

pytestmark = pytest.mark.anyio

KEY = "TEST"
VALUE = "1"


@pytest.fixture
def redis(cache_conn: Redis):
    return RedisCache(cache_conn)


async def test_get_none(redis: RedisCache):
    res = await redis.get("NONEKEY")
    assert res is None


async def test_set(redis: RedisCache):
    await redis.set(KEY, VALUE, 120)
    res = await redis.get(KEY)
    assert res == VALUE


async def test_delete(redis: RedisCache):
    await redis.set(KEY, VALUE, 120)
    res = await redis.get(KEY)
    assert res == VALUE

    await redis.delete(KEY)
    res = await redis.get(KEY)
    assert res is None


async def test_setnx(redis: RedisCache):
    value1 = "1"
    value2 = "1"

    await redis.setnx(KEY, value1, 120)
    res = await redis.get(KEY)
    assert res == value1

    await redis.setnx(KEY, value2, 120)
    res = await redis.get(KEY)
    assert res == value1  # value1 (!!!)


async def test_incr(redis: RedisCache):
    await redis.set(KEY, VALUE, 120)
    res = await redis.incr(KEY)
    assert res == 2


async def test_decr(redis: RedisCache):
    await redis.set(KEY, VALUE, 120)
    res = await redis.decr(KEY)
    assert res == 0


async def test_smembers(redis: RedisCache):
    members = await redis.smembers(KEY)
    assert isinstance(members, Iterable)
    assert len(members) == 0


async def test_sadd_single(redis: RedisCache):
    value = 1
    await redis.sadd_single(KEY, value)
    members = await redis.smembers(KEY)
    assert isinstance(members, Iterable)
    assert len(members) == 1
    assert str(VALUE) in members


async def test_sadd_multiple(redis: RedisCache):
    value1 = 1
    value2 = 2
    await redis.sadd_multiple(KEY, [value1, value2])
    members = await redis.smembers(KEY)
    assert isinstance(members, Iterable)
    assert len(members) == 2
    assert str(value1) in members
    assert str(value2) in members


async def test_sismember(redis: RedisCache):
    value = 1
    await redis.sadd_single(KEY, value)
    assert await redis.sismember(KEY, value)
    assert not await redis.sismember(KEY, value + 1)


async def test_srem(redis: RedisCache):
    value = 1
    await redis.sadd_single(KEY, value)
    assert await redis.sismember(KEY, value)
    await redis.srem(KEY, value)
    assert not await redis.sismember(KEY, value)
