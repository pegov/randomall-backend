from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Tuple

from asyncpg import Connection
from fastapi_auth import User
from sqlsl import Queries

from app.core.head import Head
from app.core.metadata import Metadata
from app.db.postgres.common import fix_user_field, was_updated
from app.models.gens import SearchParams, SearchSort
from app.utils.strings import create_random_string


class GensQ(Queries):
    get: str
    create: str
    update: str

    create_vh: str
    get_vh: str
    get_all_vh: str

    get_categories: str
    get_other_category: str
    get_subcategories: str

    get_tags: str
    get_suggestions: str

    get_likes_count: str
    get_favs_count: str
    increment_views: str

    search: str
    search_count: str
    get_stats: str


path = Path(__file__).parent / "sql" / "gen.sql"
q = GensQ().from_file(path)

MAX_VH_SIZE = 5


class GensExt:
    def __init__(self, conn: Connection) -> None:
        self._conn = conn

    async def get(self, id: int) -> Optional[dict]:
        row = await self._conn.fetchrow(q.get, id)
        if row is not None:
            return dict(
                **row,
                user={
                    "id": row.get("user_id"),
                    "username": row.get("username"),
                },
            )

        return None

    # VH

    async def create_vh(
        self,
        gen_id: int,
        user_id: int,
        title: str,
        description: str,
        access: int,
        category_id: Optional[int],
        generator_id: int,
        format: dict,
        body: dict,
        created_at: datetime,
    ) -> None:
        subcategory_ids: List[int] = await self._conn.fetchval(
            "SELECT COALESCE(array_agg(subcategory_id), ARRAY[]::integer[]) FROM gen_subcategory WHERE gen_id = $1;",
            gen_id,
        )  # type: ignore
        tag_ids: List[int] = await self._conn.fetchval(
            "SELECT COALESCE(array_agg(tag_id), ARRAY[]::integer[]) FROM gen_tag WHERE gen_id = $1;",
            gen_id,
        )  # type: ignore
        feature_ids: List[int] = await self._conn.fetchval(
            "SELECT COALESCE(array_agg(feature_id), ARRAY[]::integer[]) FROM gen_feature WHERE gen_id = $1;",
            gen_id,
        )  # type: ignore
        vh_id = await self._conn.fetchval(
            q.create_vh,
            gen_id,
            user_id,
            title,
            description,
            access,
            category_id,
            generator_id,
            format,
            body,
            created_at,
        )
        if category_id is not None and category_id != 99:
            update_obj = [
                (
                    vh_id,
                    subcategory_id,
                )
                for subcategory_id in subcategory_ids
            ]
            await self._conn.executemany(
                "INSERT INTO gen_vh_subcategory (gen_vh_id, subcategory_id) VALUES ($1, $2);",
                update_obj,
            )

        update_obj = [
            (
                vh_id,
                tag_id,
            )
            for tag_id in tag_ids
        ]
        await self._conn.executemany(
            "INSERT INTO gen_vh_tag (gen_vh_id, tag_id) VALUES ($1, $2);",
            update_obj,
        )

        update_obj = [
            (
                vh_id,
                feature_id,
            )
            for feature_id in feature_ids
        ]
        await self._conn.executemany(
            "INSERT INTO gen_vh_feature (gen_vh_id, feature_id) VALUES ($1, $2);",
            update_obj,
        )

    async def get_vh(self, id: int) -> Optional[dict]:
        row = await self._conn.fetchrow(
            q.get_vh,
            id,
        )
        if row is not None:
            row = dict(row)
            row["user"] = {
                "id": row.get("user_id"),
                "username": row.get("username"),
            }

            return row

        return None

    async def get_all_vh(self, user_id: int) -> List[dict]:
        return fix_user_field(
            await self._conn.fetch(
                q.get_all_vh,
                user_id,
            )
        )

    # EDITOR

    async def create(
        self,
        editor: User,
        head: Head,
        format: dict,
        body: dict,
        metadata: Metadata,
    ) -> int:
        async with self._conn.transaction():
            now = datetime.now(tz=timezone.utc)
            if head.category is not None:
                category_id = await self.get_category_by_name(head.category)
            else:
                category_id = None

            generator_id = 1
            features = ["num", "multiply", "list"]

            access_key = create_random_string(32)

            gen_id: int = await self._conn.fetchval(  # type: ignore
                q.create,
                editor.id,
                head.title,
                head.description,
                category_id,
                head.access,
                access_key,
                0,  # views
                True,  # active
                True,  # ads
                False,  # copyright
                metadata.hash,
                metadata.variations,
                now,  # date_added
                now,  # date_updated
                1,  # generator_id
                format,
                body,
            )  # type: ignore
            await self.update_features(gen_id, generator_id, features)
            await self.update_tags(gen_id, head.tags)  # type: ignore
            await self.update_subcategories(
                gen_id,
                category_id,
                head.subcategories,  # type: ignore
            )

            await self.create_vh(
                gen_id,
                editor.id,
                head.title,
                head.description,
                head.access,
                category_id,
                generator_id,
                format,
                body,
                now,
            )

            return gen_id

    async def update(
        self,
        id: int,
        editor: User,
        head: Head,
        format: dict,
        body: dict,
        metadata: Metadata,
    ) -> bool:
        async with self._conn.transaction():
            prev = await self.get(id)
            assert prev is not None

            user_id = prev.get("user_id")
            prev_hash = prev.get("hash")
            curr_hash = metadata.hash

            if editor.id == user_id and prev_hash != curr_hash:
                has_update = True
                now = datetime.now(tz=timezone.utc)
            else:
                has_update = False
                now = None
            if head.category is not None:
                category_id = await self.get_category_by_name(head.category)
            else:
                category_id = None

            generator_id = 1
            # features = ["num", "multiply", "list"]

            res = await self._conn.execute(
                q.update,
                id,
                head.title,
                head.description,
                category_id,
                head.access,
                metadata.hash,
                metadata.variations,
                now,
                generator_id,
                format,
                body,
            )

            # await self.update_features(id, generator_id, features)
            await self.update_tags(id, head.tags)  # type: ignore
            await self.update_subcategories(
                id,
                category_id,
                head.subcategories,  # type: ignore
            )

            if has_update:
                count: int = await self._conn.fetchval(
                    "SELECT COUNT(1) FROM gen_vh WHERE gen_id = $1;",
                    id,
                )  # type: ignore
                if count >= MAX_VH_SIZE:
                    to_delete_count = count - MAX_VH_SIZE + 1
                    res = await self._conn.execute(
                        """
                        DELETE FROM gen_vh
                        WHERE id IN (
                            SELECT id FROM gen_vh WHERE gen_id = $1 ORDER BY id ASC LIMIT $2
                        );
                        """,
                        id,
                        to_delete_count,
                    )
                await self.create_vh(
                    id,
                    user_id,  # type: ignore
                    head.title,
                    head.description,
                    head.access,
                    category_id,
                    generator_id,
                    format,
                    body,
                    now,  # type: ignore
                )

            return was_updated(res)

    async def get_category_by_name(self, name: str) -> int:
        return await self._conn.fetchval(
            "SELECT id FROM category WHERE name = $1;", name
        )  # type: ignore

    async def get_or_create_subcategory(self, category_id: int, name: str) -> int:
        id = await self._conn.fetchval(
            "SELECT id FROM subcategory WHERE category_id = $1 AND name = $2;",
            category_id,
            name,
        )
        if id is None:
            id = await self._conn.fetchval(
                "INSERT INTO subcategory(category_id, name) VALUES ($1, $2) RETURNING id;",
                category_id,
                name,
            )

        return id  # type: ignore

    async def get_or_create_tag(self, name: str) -> int:
        id = await self._conn.fetchval(
            "SELECT id FROM tag WHERE name = $1;",
            name,
        )
        if id is None:
            id = await self._conn.fetchval(
                "INSERT INTO tag(name) VALUES ($1) RETURNING id;",
                name,
            )

        return id  # type: ignore

    async def update_subcategories(
        self,
        id: int,
        category_id: Optional[int],
        subcategories: List[str],
    ) -> None:
        prev_ids: List[int] = await self._conn.fetchval(
            "SELECT COALESCE(array_agg(subcategory_id), ARRAY[]::integer[]) FROM gen_subcategory WHERE gen_id = $1;",
            id,
        )  # type: ignore
        if category_id is not None and category_id != 99:
            if subcategories is None:
                new_ids = []
            else:
                new_ids = [
                    await self.get_or_create_subcategory(category_id, name)
                    for name in subcategories
                ]
            if len(new_ids) > 0:
                await self._conn.executemany(
                    "INSERT INTO gen_subcategory(gen_id, subcategory_id) VALUES ($1, $2) ON CONFLICT DO NOTHING;",
                    [
                        (
                            id,
                            s_id,
                        )
                        for s_id in new_ids
                        if s_id not in prev_ids
                    ],
                )
            to_delete = [i for i in prev_ids if i not in new_ids]
        else:
            to_delete = prev_ids

        if len(to_delete) > 0:
            await self._conn.executemany(
                "DELETE FROM gen_subcategory WHERE gen_id = $1 AND subcategory_id = $2;",
                [
                    (
                        id,
                        sub_id,
                    )
                    for sub_id in to_delete
                ],
            )

    async def update_tags(
        self,
        id: int,
        tags: List[str],
    ) -> None:
        prev_ids: List[int] = await self._conn.fetchval(
            "SELECT COALESCE(array_agg(tag_id), ARRAY[]::integer[]) as ids FROM gen_tag WHERE gen_id = $1;",
            id,
        )  # type: ignore
        new_ids = [await self.get_or_create_tag(name) for name in tags]
        await self._conn.executemany(
            "INSERT INTO gen_tag(gen_id, tag_id) VALUES ($1, $2) ON CONFLICT DO NOTHING;",
            [
                (
                    id,
                    tag_id,
                )
                for tag_id in new_ids
                if tag_id not in prev_ids
            ],
        )

        to_delete = [i for i in prev_ids if i not in new_ids]
        await self._conn.executemany(
            "DELETE FROM gen_tag WHERE gen_id = $1 AND tag_id = $2;",
            [
                (
                    id,
                    tag_id,
                )
                for tag_id in to_delete
            ],
        )

    async def update_features(
        self,
        gen_id: int,
        eg_id: int,
        features: List[str],
    ) -> None:
        available_features = await self._conn.fetch(
            "SELECT id, name FROM feature WHERE generator_id = $1;",
            eg_id,
        )
        selected_feature_ids = [
            item.get("id")
            for item in available_features
            if item.get("name") in features
        ]
        prev_feature_ids: List[int] = await self._conn.fetchval(
            "SELECT COALESCE(array_agg(feature_id), ARRAY[]::integer[]) FROM gen_feature WHERE gen_id = $1;",
            gen_id,
        )  # type: ignore
        insert_ids = [id for id in selected_feature_ids if id not in prev_feature_ids]
        delete_ids = [id for id in prev_feature_ids if id not in selected_feature_ids]
        await self._conn.executemany(
            "INSERT INTO gen_feature(gen_id, feature_id) VALUES ($1, $2);",
            [
                (
                    gen_id,
                    f_id,
                )
                for f_id in insert_ids
            ],
        )
        await self._conn.executemany(
            "DELETE FROM gen_feature WHERE gen_id = $1 AND feature_id = $2;",
            [
                (
                    gen_id,
                    f_id,
                )
                for f_id in delete_ids
            ],
        )

    async def update_access_key(self, id: int, key: str) -> None:
        await self._conn.execute(
            "UPDATE gen SET access_key = $2 WHERE id = $1", id, key
        )

    async def activate(self, id: int) -> bool:
        res = await self._conn.execute(
            "UPDATE gen SET active = True WHERE id = $1;", id
        )
        return was_updated(res)

    async def deactivate(self, id: int) -> bool:
        res = await self._conn.execute(
            "UPDATE gen SET active = False WHERE id = $1;", id
        )
        return was_updated(res)

    # VIEW

    async def get_categories(self) -> List[dict]:
        # id, name, count
        categories = await self._conn.fetch(q.get_categories)
        other = await self._conn.fetchrow(q.get_other_category)
        # category_id, category_name, subcategory_id, subcategory_name, count
        subcategories = await self._conn.fetch(q.get_subcategories)

        res = [
            {
                "name": c_row.get("name"),
                "count": c_row.get("count"),
                "subcategories": [
                    {"name": s_row.get("name"), "count": s_row.get("count")}
                    for s_row in subcategories
                    if s_row.get("category_id") == c_row.get("id")
                ],
            }
            for c_row in categories
        ]
        res.append(
            {
                "name": other.get("name"),
                "count": other.get("count"),
            }
        )
        return res

    async def get_tags(self) -> List[dict]:
        tags = await self._conn.fetch(q.get_tags)
        return [
            {
                "name": row.get("name"),
                "count": row.get("count"),
            }
            for row in tags
        ]

    async def get_titles(self) -> List[str]:
        rows = await self._conn.fetch("SELECT title FROM gen WHERE access = 0;")
        return [row.get("title") for row in rows]

    async def get_suggestions(self, threshold: int) -> List[dict]:
        return await self._conn.fetch(
            q.get_suggestions,
            threshold,
        )

    async def toggle_like(self, id: int, user_id: int) -> bool:
        async with self._conn.transaction():
            if (
                await self._conn.fetchrow(
                    "SELECT * FROM gen_like WHERE gen_id = $1 AND user_id = $2;",
                    id,
                    user_id,
                )
                is None
            ):
                await self._conn.execute(
                    "INSERT INTO gen_like(gen_id, user_id) VALUES ($1, $2);",
                    id,
                    user_id,
                )
                return True
            else:
                await self._conn.execute(
                    "DELETE FROM gen_like WHERE gen_id = $1 AND user_id = $2;",
                    id,
                    user_id,
                )
                return False

    async def toggle_fav(self, id: int, user_id: int) -> bool:
        async with self._conn.transaction():
            if (
                await self._conn.fetchrow(
                    "SELECT * FROM gen_fav WHERE gen_id = $1 AND user_id = $2;",
                    id,
                    user_id,
                )
                is None
            ):
                await self._conn.execute(
                    "INSERT INTO gen_fav(gen_id, user_id) VALUES ($1, $2);",
                    id,
                    user_id,
                )
                return True
            else:
                await self._conn.execute(
                    "DELETE FROM gen_fav WHERE gen_id = $1 AND user_id = $2;",
                    id,
                    user_id,
                )
                return False

    async def increment_views(self, id: int) -> None:
        await self._conn.execute(q.increment_views, id)

    # SEARCH

    async def search(
        self,
        p: SearchParams,
        page_size: int,
        is_admin: bool,
    ) -> Tuple[List[dict], int]:
        match p.sort:
            case SearchSort.DATE_UPDATED:
                sort_by = "g.date_updated"
            case SearchSort.LIKES:
                sort_by = "likes_count"
            case SearchSort.VIEWS:
                sort_by = "g.views"
            case SearchSort.DATE_ADDED:
                sort_by = "g.date_added"
            case _:
                sort_by = "g.date_added"
        sort_order = "DESC"
        if is_admin:
            access = None
            active = None
        else:
            access = 0
            active = True
        query = q.search.format(sort_by, sort_order)
        offset = page_size * (p.p - 1)
        items = fix_user_field(
            await self._conn.fetch(
                query,
                offset,
                page_size,
                p.title,
                p.category,
                p.subcategories,
                p.tags,
                access,
                active,
            )
        )
        count = await self._conn.fetchval(
            q.search_count,
            p.title,
            p.category,
            p.subcategories,
            p.tags,
            access,
            active,
        )
        return items, count  # type: ignore

    # ADMIN

    async def get_stats(self) -> dict:
        return dict(await self._conn.fetchrow(q.get_stats))  # type: ignore

    async def rename_tag(self, old: str, new: str) -> bool:
        async with self._conn.transaction():
            t_id = await self._conn.fetchval(
                "SELECT id FROM tag WHERE name = $1;",
                old,
            )
            if (
                await self._conn.fetchrow(
                    "SELECT * FROM tag WHERE name = $1;",
                    new,
                )
                is not None
            ):
                return False

            await self._conn.execute(
                "UPDATE tag SET name = $2 WHERE id = $1",
                t_id,
                new,
            )
            return True

    async def rename_subcategory(self, c: str, old_sc: str, new_sc: str) -> bool:
        async with self._conn.transaction():
            c_id = await self.get_category_by_name(c)
            if (
                await self._conn.fetchrow(
                    "SELECT * FROM subcategory WHERE category_id = $1 AND name = $2;",
                    c_id,
                    new_sc,
                )
                is not None
            ):
                return False

            await self._conn.execute(
                "UPDATE subcategory SET name = $3 WHERE category_id = $1 AND name = $2;",
                c_id,
                old_sc,
                new_sc,
            )
            return True
