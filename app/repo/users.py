from typing import List, Optional

import orjson

from app.db.postgres import PostgresDB
from app.db.redis import RedisCache


class UsersRepo:
    profile_prefix = "profiles"

    def __init__(self, db: PostgresDB, cache: RedisCache) -> None:
        self._db = db
        self._cache = cache

    async def create_notification(self, user_id: int, message: str) -> None:
        await self._db.profiles.create_notification(user_id, message)

    async def get_notifications(self, user_id: int) -> List[dict]:
        return await self._db.profiles.get_notifications(user_id)

    async def see_notifications(self, user_id: int) -> None:
        await self._db.profiles.see_notifications(user_id)

    async def get_global_access_key(self, user_id: int) -> Optional[str]:
        return await self._db.profiles.get_global_access_key(user_id)

    async def set_global_access_key(self, user_id: int, key: str) -> None:
        await self._db.profiles.set_global_access_key(user_id, key)

    async def delete_global_access_key(self, user_id: int) -> None:
        await self._db.profiles.delete_global_access_key(user_id)

    async def get_profile(self, user_id: int) -> dict:
        key = f"{self.profile_prefix}:{user_id}"

        c_row = await self._cache.get(key)
        if c_row is not None:
            return orjson.loads(c_row)

        row = await self._db.profiles.get(user_id)
        await self._cache.set(
            key,
            orjson.dumps(row),
            ex=600,
        )
        return row

    async def update_description(self, user_id: int, description: str) -> None:
        await self._db.profiles.update_description(user_id, description)
        await self._cache.delete(f"{self.profile_prefix}:{user_id}")
