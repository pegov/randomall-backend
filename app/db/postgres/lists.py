from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Tuple

from asyncpg import Connection
from fastapi_auth import User
from sqlsl import Queries

from app.db.postgres.common import fix_user_field, was_updated
from app.models.lists import SearchParams


class ListsQ(Queries):
    get: str
    create: str
    update: str
    get_stats: str

    search: str
    search_count: str


path = Path(__file__).parent / "sql" / "list.sql"
q = ListsQ().from_file(path)


class ListsExt:
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
                }
            )

        return None

    async def create(self, editor: User, data: dict) -> int:
        async with self._conn.transaction():
            now = datetime.now(tz=timezone.utc)
            return await self._conn.fetchval(
                q.create,
                editor.id,
                data.get("title"),
                data.get("description"),
                data.get("access"),
                data.get("content"),
                data.get("slicer"),
                now,
                now,
                True,  # active
            )  # type: ignore

    async def update(self, id: int, editor: User, data: dict) -> bool:
        async with self._conn.transaction():
            prev = await self.get(id)
            assert prev is not None

            user_id = prev.get("user_id")
            if editor.id == user_id:
                now = datetime.now(tz=timezone.utc)
            else:
                now = None

            await self._conn.execute(
                q.update,
                id,
                data.get("title"),
                data.get("description"),
                data.get("access"),
                data.get("content"),
                data.get("slicer"),
                now,
            )
            return True

    async def deactivate(self, id: int) -> bool:
        res = await self._conn.execute(
            "UPDATE list SET active = False WHERE id = $1;",
            id,
        )
        return was_updated(res)

    async def activate(self, id: int) -> bool:
        res = await self._conn.execute(
            "UPDATE list SET active = True WHERE id = $1;",
            id,
        )
        return was_updated(res)

    async def search(
        self,
        p: SearchParams,
        page_size: int,
        is_admin: bool,
    ) -> Tuple[List[dict], int]:
        sort_by = "l.id"
        sort_order = "DESC"
        if is_admin:
            access = None
        else:
            access = 0
        query = q.search.format(sort_by, sort_order)
        offset = page_size * (p.p - 1)
        items = fix_user_field(
            await self._conn.fetch(
                query,
                offset,
                page_size,
                p.title,
                access,
            )
        )
        count = await self._conn.fetchval(
            q.search_count,
            p.title,
            access,
        )
        return items, count  # type: ignore

    async def get_stats(self) -> dict:
        return dict(await self._conn.fetchrow(q.get_stats))  # type: ignore
