from typing import List, Optional, Tuple

from fastapi_auth import User

from app.db.postgres import PostgresDB
from app.db.redis import RedisCache
from app.entities.events import Ev
from app.logger import Logger
from app.models.events import SearchParams


class EventsRepo:
    def __init__(
        self,
        db: PostgresDB,
        cache: RedisCache,
        logger: Logger = None,  # type: ignore
    ) -> None:
        self._db = db
        self._cache = cache
        self._logger = logger

    async def create(
        self,
        ev: Ev,
        data: dict,
        user: Optional[User] = None,
    ) -> None:
        if ev.db:
            user_id = user.id if user is not None else 0
            await self._db.events.create(ev, data, user_id)
        if ev.log:
            if user is not None:
                data = {"user_id": user.id, **data}
            self._logger.event(ev, data)

    async def search(self, sp: SearchParams) -> Tuple[List[dict], int, int]:
        return await self._db.events.search(sp)

    async def delete(self, id: int) -> None:
        await self._db.events.delete(id)

    async def clear(self) -> None:
        await self._db.events.clear()
