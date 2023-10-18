import asyncio

import socket
from typing import Callable
import uuid
import pytest
import docker as libdocker
from fastapi_auth import User

pytest_plugins = ["db_fixtures", "cache_fixtures"]


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


# @pytest.fixture(scope="session")
# def event_loop():
#     policy = asyncio.get_event_loop_policy()
#     loop = policy.new_event_loop()
#     yield loop
#     loop.close()


@pytest.fixture(scope="session")
def session_id() -> str:
    return str(uuid.uuid4())


@pytest.fixture(scope="session")
def unused_port() -> Callable[[], int]:
    def f():
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(
                (
                    "127.0.0.1",
                    0,
                )
            )
            return s.getsockname()[1]

    return f


class DockerConfig:
    db_port: int
    cache_port: int


@pytest.fixture(scope="session")
def docker_config():
    return DockerConfig()


@pytest.fixture(scope="session")
def docker() -> libdocker.DockerClient:
    return libdocker.from_env()


@pytest.fixture
def model_user_admin():
    return User(
        id=1,
        username="admin",
        roles=[],
        permissions=[],
        iat=0,
        exp=0,
        type="access",
    )
