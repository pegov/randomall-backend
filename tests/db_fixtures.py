from typing import Callable
from datetime import datetime, timezone
import json
import time
import pytest
import docker as libdocker

from asyncpg import connect, Connection, create_pool

from fastapi_auth.backend.password.passlib import PasslibPasswordBackend

URL = "postgres://postgres:postgres@localhost:{}/test"

password_backend = PasslibPasswordBackend()


async def init_db(conn: Connection):
    with open("./migrations/01_init.sql") as f:
        queries = f.read()
    await conn.execute(queries)
    now = datetime.now(tz=timezone.utc)
    await conn.execute(
        """
        INSERT INTO auth_user (
            username,
            email,
            password,
            active,
            verified,
            created_at,
            last_login
        ) VALUES ($1, $2, $3, $4, $5, $6, $7);
        """,
        "admin",
        "admin@gmail.com",
        password_backend.hash("hunter2"),
        True,
        True,
        now,
        now,
    )
    await conn.execute(
        """
        INSERT INTO generator(name) VALUES ($1);
        """,
        "blocks",
    )
    await conn.execute(
        """
        INSERT INTO category(name) VALUES ($1);
        """,
        "Игры",
    )


async def ping_db(port: int):
    timeout = 0.001
    for _ in range(1000):
        try:
            conn: Connection = await connect(URL.format(port))
            await init_db(conn)
            await conn.close()
            return
        except Exception as e:
            time.sleep(timeout)
            timeout *= 2
    else:
        raise RuntimeError("cannot connect to postgres")


async def clear_db(conn: Connection):
    await conn.execute(
        """
        DROP SCHEMA public CASCADE;
        CREATE SCHEMA public;
        GRANT ALL ON SCHEMA public TO postgres;
        GRANT ALL ON SCHEMA public TO public;
        COMMENT ON SCHEMA public IS 'standard public schema';
        """
    )


@pytest.fixture(scope="session")
async def db_server(
    unused_port: Callable[[], int],
    session_id: str,
    docker: libdocker.DockerClient,
    docker_config,
):
    docker.images.pull("postgres:14.4")
    port = unused_port()
    container = docker.containers.run(
        image="postgres:14.4",
        command="postgres -c fsync=off -c full_page_writes=off",
        detach=True,
        name=f"test-postgres-{session_id}",
        ports={
            5432: port,
        },
        environment={
            "POSTGRES_DB": "test",
            "POSTGRES_USER": "postgres",
            "POSTGRES_PASSWORD": "postgres",
        },
    )
    try:
        await ping_db(port)
        docker_config.db_port = port
        yield container
    finally:
        container.kill()
        container.remove()


@pytest.fixture(scope="session")
async def db_pool(db_server, docker_config):
    port = docker_config.db_port
    url = URL.format(port)
    async with create_pool(url) as pool:
        yield pool


@pytest.fixture
async def db_conn(db_pool):
    async with db_pool.acquire() as conn:
        tr = conn.transaction()
        await conn.set_type_codec(
            "jsonb",
            encoder=json.dumps,
            decoder=json.loads,
            schema="pg_catalog",
        )
        await tr.start()
        try:
            yield conn
        finally:
            await tr.rollback()
