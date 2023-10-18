import os

import aioredis
import asyncpg
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse
from starlette.middleware.sessions import SessionMiddleware

from app.config import (
    API_USERS_PREFIX,
    CACHE_URL,
    DATABASE_HOST,
    DATABASE_NAME,
    DATABASE_PASSWORD,
    DATABASE_PORT,
    DATABASE_USERNAME,
    DEBUG,
    DOMAIN,
    LANGUAGE,
    LEGACY_API_CUSTOM_GENS_PREFIX,
    SECRET_KEY,
    VERSION,
)
from app.db.postgres import PostgresDB
from app.db.redis import RedisCache
from app.logger import Logger
from app.repo.settings import SettingsRepo

os.system("color")


def get_app() -> FastAPI:
    app = FastAPI(
        title=DOMAIN,
        debug=DEBUG,
        version=VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        default_response_class=ORJSONResponse,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(SessionMiddleware, secret_key=str(SECRET_KEY), max_age=600)

    app.state.logger = Logger()

    from app.auth import get_auth_app

    async def open_connection():
        db_dsn = f"postgres://{DATABASE_USERNAME}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}"
        app.state.db_pool = await asyncpg.create_pool(db_dsn)
        cache_dsn = CACHE_URL
        app.state.cache_pool = aioredis.from_url(cache_dsn, decode_responses=True)
        if DEBUG:
            await app.state.cache_pool.flushdb()

        async with app.state.db_pool.acquire() as db_conn:
            async with app.state.cache_pool.client() as cache_conn:
                pg = PostgresDB(db_conn)
                rs = RedisCache(cache_conn)
                settings_repo = SettingsRepo(pg, rs)
                await settings_repo.on_startup()

    async def close_connection():
        await app.state.db_pool.close()

    app.add_event_handler("startup", open_connection)
    app.add_event_handler("shutdown", close_connection)

    # ---- AUTH ----
    auth_app = get_auth_app(app)
    auth_app.include_routers(API_USERS_PREFIX)

    from app.routers.dev import router as dev_router
    from app.routers.events import router as events_router
    from app.routers.gens import router as gens_router
    from app.routers.lists import router as lists_router
    from app.routers.profiles import router as profiles_router
    from app.routers.settings import router as settings_router
    from app.routers.users import router as users_router

    app.include_router(users_router, prefix=API_USERS_PREFIX)
    app.include_router(profiles_router)  # already has prefix
    app.include_router(gens_router)  # already has prefix
    app.include_router(dev_router)
    app.include_router(lists_router)  # already has prefix
    app.include_router(settings_router, prefix="/api/settings")
    app.include_router(events_router, prefix="/api/events")

    if LANGUAGE == "RU":
        from app.routers.gens.view import router as legacy_custom_gens_router

        app.include_router(
            legacy_custom_gens_router, prefix=LEGACY_API_CUSTOM_GENS_PREFIX
        )

        from app.routers.general import router as general_router

        app.include_router(general_router)  # already has prefix

    return app


app = get_app()
