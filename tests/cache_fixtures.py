from typing import Callable
import time
import pytest
import docker as libdocker

import aioredis


async def ping_cache(port: int):
    timeout = 0.001
    client = aioredis.from_url(f"redis://localhost:{port}/")
    async with client.client() as conn:
        for _ in range(1000):
            try:
                print("PINGING CACHE")
                if await conn.ping():
                    return
                else:
                    time.sleep(timeout)
                    timeout *= 2
            except Exception as e:
                print(e)
            finally:
                await client.close()

        else:
            raise RuntimeError("cannot connect to redis")


@pytest.fixture(scope="session")
async def cache_server(
    unused_port: Callable[[], int],
    session_id: str,
    docker: libdocker.DockerClient,
    docker_config,
):
    docker.images.pull("redis:alpine")
    port = unused_port()
    container = docker.containers.run(
        image="redis",
        detach=True,
        name=f"test-redis-{session_id}",
        ports={
            6379: port,
        },
    )
    try:
        await ping_cache(port)
        docker_config.cache_port = port
        yield container
    finally:
        container.kill()
        container.remove()


@pytest.fixture(scope="session")
async def cache_pool(cache_server, docker_config):
    port = docker_config.cache_port
    pool = aioredis.from_url(
        f"redis://localhost:{port}/",
        decode_responses=True,
    )
    yield pool


@pytest.fixture
async def cache_conn(cache_pool):
    yield cache_pool
    await cache_pool.flushdb()
