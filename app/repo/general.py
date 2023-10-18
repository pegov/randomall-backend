import time
from typing import Any, Callable, List, Optional, Tuple

import orjson

from app.db.postgres import PostgresDB
from app.db.redis import RedisCache


class GeneralRepo:
    info_key: str = "general:info"
    ban_prefix: str = "general:ratelimit_ban"
    ratelimit_prefix: str = "general:ratelimit"

    def __init__(self, db: PostgresDB, cache: RedisCache) -> None:
        self._db = db
        self._cache = cache

    async def _get(self, key: str, call: Callable, *args) -> Any:
        cached_item = await self._cache.get(key)
        if cached_item is not None:
            return orjson.loads(cached_item)

        item = await call(*args)
        await self._cache.set(
            key,
            orjson.dumps(item),
            ex=3600,
        )
        return item

    async def get_info(self, name: str) -> dict:
        return await self._get(
            f"{self.info_key}:{name}",
            self._db.general.get_info,
            name,
        )

    async def get_all_info(self) -> List[dict]:
        return await self._get(self.info_key, self._db.general.get_all_info)

    async def in_ratelimit_ban(self, ip: str) -> bool:
        key = f"{self.ban_prefix}:{ip}"
        return bool(await self._cache.get(key))

    async def ratelimit_exceeded(self, ip: str, limit: int) -> bool:
        ts = int(time.time())
        key = f"{self.ratelimit_prefix}:{ip}:{ts}"
        ratelimit = await self._cache.get(key)

        if ratelimit is not None:
            ratelimit = int(ratelimit)  # type: ignore
            if ratelimit > limit:  # type: ignore
                ban_key = f"{self.ban_prefix}:{ip}"
                await self._cache.set(ban_key, 1, ex=4)
                return True
        else:
            await self._cache.set(key, 1, ex=2)

        await self._cache.incr(key)
        return False

    async def _delete_plot_count_from_cache(self) -> None:
        await self._cache.delete(f"{self.info_key}:plot:count")

    async def get_plot_count(self) -> dict:
        return await self._get(
            f"{self.info_key}:plot:count", self._db.general.get_plot_count
        )

    async def create_usergen(self, data: dict) -> None:
        await self._db.general.suggest(data)
        if data.get("name") == "plot":
            await self._delete_plot_count_from_cache()

    async def has_same_usergen(self, name: str, value: str) -> bool:
        return await self._db.general.usergen_has_value(name, value)

    async def get_stats(self) -> dict:
        return await self._db.general.get_stats()

    async def get_first_unchecked_usergen(
        self,
    ) -> Optional[Tuple[dict, List[dict]]]:
        item = await self._db.general.get_first_unchecked_usergen()
        if item is None:
            return None

        similar = await self._db.general.get_similar_usergen(
            item.get("name"),
            item.get("value"),
        )
        return item, similar

    async def get_usergen_count(self) -> int:
        return await self._db.general.get_unchecked_usergen_count()

    async def get_wp_count(self) -> int:
        return await self._db.general.get_unchecked_wp_count()

    async def check(self, data: dict) -> None:
        data.update({"checked": True})
        await self._db.general.check(data)
        if data.get("name") == "plot":
            await self._delete_plot_count_from_cache()

    async def check_wp(self, data: dict) -> None:
        data.update({"checked": True})
        await self._db.general.check_wp(data)
        await self._delete_plot_count_from_cache()

    async def uncheck(self, name: str, id: int, valid: bool) -> None:
        if valid:
            await self._db.general.uncheck_actual(name, id)
        else:
            await self._db.general.uncheck_invalid(name, id)

    async def uncheck_wp(self, id: int, valid: bool) -> None:
        if valid:
            await self._db.general.uncheck_actual_wp(id)
        else:
            await self._db.general.uncheck_invalid_wp(id)

    async def get_first_unchecked_wp(self) -> Optional[dict]:
        return await self._db.general.get_first_unchecked_wp()

    async def get_last_checked_usergen(self, count: int) -> List[dict]:
        return await self._db.general.get_last_checked_usergen(count)

    async def get_last_checked_wp(self, count: int) -> List[dict]:
        return await self._db.general.get_last_checked_wp(count)

    async def toggle_usergen(self, name: str) -> None:
        await self._db.general.toggle_usergen(name)
        await self._cache.delete(self.info_key)
        await self._cache.delete(f"{self.info_key}:{name}")

    async def get_general_result(self, name: str, data: Optional[dict] = None) -> Any:
        return await self._db.general.get_general_result(name, data)

    async def get_creative_result(
        self,
        name: str,
        data: Optional[Any] = None,
        count: int = 1,
    ) -> Any:
        return await self._db.general.get_creative_result(name, data, count)
