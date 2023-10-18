import asyncio
import json

from aioredis import Redis
from asyncpg import Connection, Pool
from fastapi import Depends, Request
from fastapi_auth.backend.cache.redis import RedisClient
from fastapi_auth.backend.db.postgres import PostgresClient
from fastapi_auth.repo import Repo as AuthRepo

from app.config import DOMAIN, LANGUAGE, ORIGIN
from app.db.postgres import PostgresDB
from app.db.redis import RedisCache
from app.logger import Logger
from app.repo.events import EventsRepo
from app.repo.general import GeneralRepo
from app.repo.gens import GensRepo
from app.repo.lists import ListsRepo
from app.repo.settings import SettingsRepo
from app.repo.users import UsersRepo
from app.telegram import TelegramNotifier


def get_notifier() -> TelegramNotifier:  # pragma: no cover
    return TelegramNotifier(DOMAIN, ORIGIN, LANGUAGE)


def get_logger(request: Request) -> Logger:
    return request.app.state.logger


def _get_db_pool(request: Request) -> Pool:
    return request.app.state.db_pool


def _get_cache_pool(request: Request) -> Redis:
    return request.app.state.cache_pool


async def _get_connection_from_db_pool(pool: Pool = Depends(_get_db_pool)):
    async with pool.acquire() as connection:
        await connection.set_type_codec(
            "jsonb",
            encoder=json.dumps,
            decoder=json.loads,
            schema="pg_catalog",
        )
        yield connection


async def _get_connection_from_cache_pool(pool: Redis = Depends(_get_cache_pool)):
    async with pool.client() as connection:
        yield connection


def get_repo(
    repo_type,
):
    async def _get_repo(
        db_connection: Connection = Depends(_get_connection_from_db_pool),
        cache_connection: Redis = Depends(_get_connection_from_cache_pool),
    ):
        pg = PostgresDB(db_connection)
        redis = RedisCache(cache_connection)
        repo = repo_type(pg, redis)
        yield repo
        coros = []
        if hasattr(repo, "background_tasks") and len(repo.background_tasks) > 0:
            coros.extend(repo.background_tasks)
        if len(pg.background_tasks) > 0:
            coros.extend(pg.background_tasks)
        if len(redis.background_tasks) > 0:
            coros.extend(redis.background_tasks)

        await asyncio.gather(*coros)

    return _get_repo


_get_general_repo = get_repo(GeneralRepo)
_get_gens_repo = get_repo(GensRepo)
_get_lists_repo = get_repo(ListsRepo)
_get_settings_repo = get_repo(SettingsRepo)
_get_users_repo = get_repo(UsersRepo)
_get_events_repo = get_repo(EventsRepo)


def get_general_repo(repo=Depends(_get_general_repo)):
    return repo


def get_gens_repo(repo=Depends(_get_gens_repo)):
    return repo


def get_lists_repo(repo=Depends(_get_lists_repo)):
    return repo


def get_settings_repo(repo=Depends(_get_settings_repo)):
    return repo


def get_users_repo(repo=Depends(_get_users_repo)):
    return repo


def get_events_repo(repo=Depends(_get_events_repo), logger=Depends(get_logger)):
    repo._logger = logger
    return repo


def get_fastapi_auth_repo(
    request: Request,
    db_connection=Depends(_get_connection_from_db_pool),
    cache_connection=Depends(_get_connection_from_cache_pool),
) -> AuthRepo:
    tp = request.app.state._fastapi_auth._token_params
    db_client = PostgresClient(db_connection)
    cache_client = RedisClient(cache_connection)
    repo = AuthRepo(db_client, cache_client, tp)
    return repo
