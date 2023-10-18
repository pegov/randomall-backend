import asyncio
import time
from typing import List, Optional, Tuple

import orjson
from fastapi_auth import User

from app.config import DEBUG
from app.core.head import Head
from app.core.metadata import Metadata
from app.db.postgres import PostgresDB
from app.db.redis import RedisCache
from app.entities.gens import GeneratorEntity
from app.models.gens import SearchParams, SearchSort, Suggestion
from app.utils.strings import create_random_string

SESSIONS_PER_USER = 15


class GensRepo:
    prefix = "gens"
    views_prefix: str = "gens:views"
    likes_prefix: str = "gens:likes"
    favs_prefix: str = "gens:favs"
    likes_count_prefix: str = "gens:likes_count"
    favs_count_prefix: str = "gens:favs_count"
    preview_key: str = "gens:preview"
    categories_key: str = "gens:categories"
    tags_key: str = "gens:tags"

    editor_rate_key: str = "gens:editor_rate"

    create_session_prefix: str = "gens:session:create"
    edit_session_prefix: str = "gens:session:edit"

    def __init__(self, db: PostgresDB, cache: RedisCache) -> None:
        self._db = db
        self._cache = cache

    async def get(self, id: int) -> Optional[GeneratorEntity]:
        row_key = f"{self.prefix}:{id}"
        views_key = f"{self.views_prefix}:{id}"
        likes_key = f"{self.likes_prefix}:{id}"
        favs_key = f"{self.favs_prefix}:{id}"
        likes_count_key = f"{self.likes_count_prefix}:{id}"
        favs_count_key = f"{self.favs_count_prefix}:{id}"

        c_row = await self._cache.get(row_key)
        if c_row is None:
            row = await self._db.gens.get(id)
            if row is None:
                return None

            await self._cache.set(
                row_key,
                orjson.dumps(row),
                120,
            )
            await self._cache.set(
                views_key,
                row.get("views"),  # type: ignore
                140,
            )
            await self._cache.delete(likes_key)
            await self._cache.sadd_multiple(
                likes_key,
                row.get("likes"),  # type: ignore
            )
            await self._cache.delete(favs_key)
            await self._cache.sadd_multiple(
                favs_key,
                row.get("favs"),  # type: ignore
            )
            await self._cache.set(
                favs_count_key,
                row.get("favs_count"),  # type: ignore
                140,
            )
            await self._cache.set(
                likes_count_key,
                row.get("likes_count"),  # type: ignore
                140,
            )
            return GeneratorEntity(**row)

        c_views = await self._cache.get(views_key)
        c_likes = await self._cache.smembers(likes_key)
        c_favs = await self._cache.smembers(favs_key)
        c_likes_count = await self._cache.get(likes_count_key)
        c_favs_count = await self._cache.get(favs_count_key)

        assert c_views is not None
        assert c_likes_count is not None
        assert c_favs_count is not None

        row = orjson.loads(c_row)
        views = int(c_views)
        likes = [int(v) for v in c_likes]
        favs = [int(v) for v in c_favs]
        likes_count = int(c_likes_count)
        favs_count = int(c_favs_count)
        row["views"] = views
        row["likes"] = likes
        row["favs"] = favs
        row["likes_count"] = likes_count
        row["favs_count"] = favs_count
        return GeneratorEntity(**row)

    async def reset_cache(self, id: int) -> None:
        await self._cache.delete(f"{self.prefix}:{id}")
        await self._cache.delete(f"{self.likes_prefix}:{id}")
        await self._cache.delete(f"{self.favs_prefix}:{id}")

    async def get_all_vh(self, user_id: int) -> List[dict]:
        return await self._db.gens.get_all_vh(user_id)

    async def get_vh(self, id: int) -> Optional[dict]:
        return await self._db.gens.get_vh(id)

    async def get_editor_rate(self) -> int:
        res = await self._cache.get(self.editor_rate_key)
        if res is not None:
            return int(res)

        return 0

    async def create(
        self,
        editor: User,
        head: Head,
        format: dict,
        body: dict,
        metadata: Metadata,
    ) -> int:
        res = await self._db.gens.create(editor, head, format, body, metadata)
        if head.access == 0:
            await self.reset_preview()
            await self.reset_categories()

        await self._cache.setnx(self.editor_rate_key, 0, ex=3600)
        await self._cache.incr(self.editor_rate_key)

        return res

    async def update(
        self,
        id: int,
        editor: User,
        head: Head,
        format: dict,
        body: dict,
        metadata: Metadata,
    ) -> bool:
        res = await self._db.gens.update(id, editor, head, format, body, metadata)
        await self.reset_cache(id)
        await self.reset_preview()
        await self.reset_categories()
        return res

    async def delete(self, id: int) -> bool:
        res = await self._db.gens.deactivate(id)
        await self.reset_cache(id)
        await self.reset_preview()
        await self.reset_categories()
        return res

    # SEARCH
    async def search_and_count(
        self,
        search_params: SearchParams,
        limit: int,
        is_admin: bool,
    ) -> Tuple[List[dict], int]:
        return await self._db.gens.search(search_params, limit, is_admin)

    async def get_categories_and_count(self) -> List[dict]:
        c_categories = await self._cache.get(self.categories_key)
        if c_categories is not None:
            return orjson.loads(c_categories)

        categories = await self._db.gens.get_categories()
        self._cache.background(
            self._cache.set(self.categories_key, orjson.dumps(categories), 600)
        )
        return categories

    async def reset_categories(self) -> None:
        await self._cache.delete(self.categories_key)

    async def get_new_public(self, count: int) -> List[dict]:
        c_items = await self._cache.get(self.preview_key)
        if c_items is not None:
            return orjson.loads(c_items)

        p = SearchParams(sort=SearchSort.DATE_UPDATED)  # type: ignore
        items, _ = await self._db.gens.search(
            p,
            count,
            False,
        )
        self._cache.background(
            self._cache.set(self.preview_key, orjson.dumps(items), 600)
        )
        return items

    def reset_preview_in_background(self) -> None:
        self._cache.background(self._cache.delete(self.preview_key))

    async def reset_preview(self) -> None:
        await self._cache.delete(self.preview_key)

    async def get_sorted_public_tags_and_count(self) -> List[dict]:
        c_items = await self._cache.get(self.tags_key)
        if c_items is not None:
            return orjson.loads(c_items)

        items = await self._db.gens.get_tags()
        self._cache.background(self._cache.set(self.tags_key, orjson.dumps(items), 600))
        return items

    async def reset_tags(self) -> None:
        await self._cache.delete(self.tags_key)

    async def get_titles(self) -> List[str]:
        key = f"{self.prefix}:titles"
        c_values = await self._cache.get(key)
        if c_values is not None:
            return orjson.loads(c_values)

        values = await self._db.gens.get_titles()
        self._cache.background(self._cache.set(key, orjson.dumps(values), 600))
        return values

    async def get_suggestions(self, threshold: int) -> List[dict]:
        key = f"{self.prefix}:suggestions"
        cache = await self._cache.get(key)
        if cache is not None:
            return orjson.loads(cache)

        items = await self._db.gens.get_suggestions(threshold)

        suggestions = [
            Suggestion(
                id=item.get("id"),  # type: ignore
                title=item.get("title"),  # type: ignore
                likes_count=item.get("likes_count"),  # type: ignore
            ).dict(by_alias=True)
            for item in items
        ]

        self._cache.background(
            self._cache.set(key, orjson.dumps(suggestions), 600),
        )

        return suggestions

    # VIEW

    def increment_views(self, id: int) -> None:
        self._db.background(self._db.gens.increment_views(id))
        key = f"{self.views_prefix}:{id}"
        self._cache.background(self._cache.incr(key))

    async def change_access_key(self, id: int, new_access_key: str) -> None:
        await self._db.gens.update_access_key(id, new_access_key)
        await self.reset_cache(id)

    async def in_ratelimit_ban(self, ip: str) -> bool:
        key = f"{self.prefix}:ratelimit_ban:{ip}"
        return bool(await self._cache.get(key))

    async def ratelimit_exceeded(self, ip: str, ratelimit: int) -> bool:
        if DEBUG:
            return False

        ts = int(time.time())
        key = f"{self.prefix}:ratelimit:{ip}:{ts}"

        rate = await self._cache.get(key)

        if rate is not None:  # pragma: no cover
            rate = int(rate)  # type: ignore
            if rate > ratelimit:  # type: ignore
                ban_key = f"{self.prefix}:ratelimit_ban:{ip}"
                await self._cache.set(ban_key, 1, ex=4)
                return True

        else:
            await self._cache.set(key, 1, ex=2)

        await self._cache.incr(key)
        return False

    # EDITOR

    async def ping(self, id: int, user_id: int, interval: int) -> None:
        key = f"{self.prefix}:ping:{user_id}"
        self._cache.background(self._cache.set(key, id, interval))

    @staticmethod
    def _sort_dict_by_value(d: dict) -> dict:
        return dict(sorted(d.items(), key=lambda i: i[1]))

    async def _new_session(self, user_id: int, prefix: str) -> str:
        keys = await self._cache.keys(f"{prefix}:{user_id}:*")
        values = await self._cache.mget(keys)

        d = self._sort_dict_by_value(dict(zip(keys, values)))
        c = len(d)

        if c > SESSIONS_PER_USER:
            to_delete = c - SESSIONS_PER_USER
            for key in list(d.keys())[0:to_delete]:
                await self._cache.delete(key)

        session = create_random_string(32)
        ts = int(time.time())
        await self._cache.set(
            f"{prefix}:{user_id}:{session}",
            ts,
            60 * 60 * 8,
        )
        return session

    async def new_create_session(self, user_id: int) -> str:
        return await self._new_session(user_id, self.create_session_prefix)

    async def new_edit_session(self, user_id: int) -> str:
        return await self._new_session(user_id, self.edit_session_prefix)

    async def _get_session(
        self,
        user_id: int,
        session: str,
        prefix: str,
    ) -> Optional[str]:
        return await self._cache.get(f"{prefix}:{user_id}:{session}")

    async def get_create_session(self, user_id: int, session: str) -> Optional[str]:
        return await self._get_session(user_id, session, self.create_session_prefix)

    async def get_edit_session(self, user_id: int, session: str) -> Optional[str]:
        return await self._get_session(user_id, session, self.edit_session_prefix)

    async def _delete_session(self, user_id: int, session: str, prefix: str) -> None:
        return await self._cache.delete(f"{prefix}:{user_id}:{session}")

    async def delete_create_session(self, user_id: int, session: str) -> None:
        await self._delete_session(user_id, session, self.create_session_prefix)

    async def delete_edit_session(self, user_id: int, session: str) -> None:
        await self._delete_session(user_id, session, self.edit_session_prefix)

    async def get_backup(self, user_id: int) -> Optional[str]:
        key = f"{self.prefix}:editor:{user_id}"
        return await self._cache.get(key)

    async def create_backup(self, user_id: int, data: str) -> None:
        key = f"{self.prefix}:editor:{user_id}"
        self._cache.background(self._cache.set(key, orjson.dumps(data), 900))

    # ADMIN

    async def get_pings(self) -> List[dict]:
        keys = await self._cache.keys(f"{self.prefix}:ping:*")
        users = []
        for key in keys:
            _, _, user_id = key.split(":")  # type: ignore
            id = await self._cache.get(key)  # type: ignore
            users.append({"user_id": user_id, "gen_id": id})
        return users

    async def get_stats(self) -> dict:
        return await self._db.gens.get_stats()

    # PROFILE

    async def get_profile_for_owner(self, user_id: int) -> List[dict]:
        return await self._db.profiles.get_gens_for_owner(user_id)

    async def get_profile_for_guest(self, user_id: int) -> List[dict]:
        return await self._db.profiles.get_gens_for_guest(user_id)

    async def get_profile_favs(self, user_id: int) -> List[dict]:
        return await self._db.profiles.get_gens_fav(user_id)

    async def like(self, id: int, user_id: int) -> None:
        count_key = f"{self.likes_count_prefix}:{id}"
        set_key = f"{self.likes_prefix}:{id}"
        if await self._db.gens.toggle_like(id, user_id):
            self._cache.background(self._cache.incr(count_key))
            self._cache.background(self._cache.sadd_single(set_key, user_id))
        else:
            self._cache.background(self._cache.decr(count_key))
            self._cache.background(self._cache.srem(set_key, user_id))

    async def fav(self, id: int, user_id: int) -> None:
        count_key = f"{self.favs_count_prefix}:{id}"
        set_key = f"{self.favs_prefix}:{id}"
        if await self._db.gens.toggle_fav(id, user_id):
            self._cache.background(self._cache.incr(count_key))
            self._cache.background(self._cache.sadd_single(set_key, user_id))
        else:
            self._cache.background(self._cache.decr(count_key))
            self._cache.background(self._cache.srem(set_key, user_id))

    async def get_sitemap(self) -> List[dict]:
        return await self._db.internal.get_sitemap()

    async def _reset_cache_many(self, p: SearchParams) -> None:
        items, _ = await self._db.gens.search(
            p,
            page_size=999_999_999,
            is_admin=True,
        )
        gen_ids = [item.get("id") for item in items]

        tasks = []
        for gen_id in gen_ids:
            tasks.append(asyncio.create_task(self.reset_cache(gen_id)))  # type: ignore

        tasks.append(asyncio.create_task(self.reset_preview()))
        await asyncio.gather(*tasks)

    async def rename_tag(self, old_name: str, new_name: str) -> bool:
        if not await self._db.gens.rename_tag(old_name, new_name):
            return False

        p = SearchParams(t=[new_name])  # type: ignore
        await self._reset_cache_many(p)
        await self.reset_tags()
        return True

    async def rename_subcategory(
        self,
        category_name: str,
        old_subcategory_name: str,
        new_subcategory_name: str,
    ) -> bool:
        if not await self._db.gens.rename_subcategory(
            category_name,
            old_subcategory_name,
            new_subcategory_name,
        ):
            return False

        p = SearchParams(  # type: ignore
            c=category_name,
            sc=[old_subcategory_name],
        )
        await self._reset_cache_many(p)
        await self.reset_categories()
        return True
