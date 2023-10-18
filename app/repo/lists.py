from typing import List, Optional, Tuple

import orjson
from fastapi_auth import User

from app.db.postgres import PostgresDB
from app.db.redis import RedisCache
from app.entities.lists import ListEntity
from app.models.lists import SearchParams


class ListsRepo:
    prefix = "lists"

    def __init__(self, db: PostgresDB, cache: RedisCache) -> None:
        self._db = db
        self._cache = cache

    async def get(self, id: int) -> Optional[ListEntity]:
        key = f"{self.prefix}:{id}"
        c_row = await self._cache.get(key)
        if c_row is None:
            row = await self._db.lists.get(id)
            if row is None:
                return None

            row = dict(row)

            self._cache.background(self._cache.set(key, orjson.dumps(row), 600))
            return ListEntity(**row)

        row = orjson.loads(c_row)
        return ListEntity(**row)

    async def reset_cache(self, id: int) -> None:
        await self._cache.delete(f"{self.prefix}:{id}")

    async def create(self, editor: User, data: dict) -> int:
        id = await self._db.lists.create(editor, data)
        return id

    async def update(self, id: int, editor: User, data: dict) -> bool:
        res = await self._db.lists.update(id, editor, data)
        await self.reset_cache(id)
        return res

    async def search_and_count(
        self,
        search_params: SearchParams,
        limit: int,
        is_admin: bool,
    ) -> Tuple[List[dict], int]:
        return await self._db.lists.search(search_params, limit, is_admin)

    async def get_profile_for_owner(self, user_id: int) -> List[dict]:
        return await self._db.profiles.get_lists_for_owner(user_id)

    async def get_profile_for_guest(self, user_id: int) -> List[dict]:
        return await self._db.profiles.get_lists_for_guest(user_id)

    async def get_stats(self) -> dict:
        return await self._db.lists.get_stats()

    async def activate(self, id: int) -> bool:
        res = await self._db.lists.activate(id)
        if res:
            await self.reset_cache(id)
        return res

    async def deactivate(self, id: int) -> bool:
        res = await self._db.lists.deactivate(id)
        if res:
            await self.reset_cache(id)
        return res
