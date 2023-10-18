from pathlib import Path
from typing import List, Tuple

from asyncpg import Connection
from sqlsl import Queries

from app.db.postgres.common import fix_user_field, get_offset, get_pages
from app.entities.events import Ev
from app.models.events import SearchParams


class EventsQ(Queries):
    search: str
    search_count: str
    get_by_user_id_and_name: str


path = Path(__file__).parent / "sql" / "event.sql"
q = EventsQ().from_file(path)


class EventsExt:
    def __init__(self, conn: Connection) -> None:
        self._conn = conn

    async def create(self, ev: Ev, data: dict, user_id: int) -> None:
        async with self._conn.transaction():
            if ev.replace:
                await self._conn.execute(
                    "DELETE FROM user_event WHERE user_id = $1 AND name = $2;",
                    user_id,
                    ev.name,
                )
            await self._conn.fetchval(  # type: ignore
                "INSERT INTO user_event (user_id, name, data) VALUES ($1, $2, $3);",
                user_id,
                ev.name,
                data,
            )

    async def search(self, sp: SearchParams) -> Tuple[List[dict], int, int]:
        sort_by = "created_at"
        sort_order = "DESC"

        query = q.search.format(sort_by, sort_order)
        offset = get_offset(sp.size, sp.p)

        items = fix_user_field(
            await self._conn.fetch(
                query,
                offset,
                sp.size,
                sp.user_id,
                # sp.names,
            )
        )
        count: int = await self._conn.fetchval(  # type: ignore
            q.search_count,
            offset,
            sp.size,
            sp.user_id,
            # sp.names,
        )
        pages = get_pages(count, sp.size)
        return items, count, pages

    async def delete(self, id: int) -> None:
        await self._conn.execute(
            "DELETE FROM user_event WHERE id = $1;",
            id,
        )

    async def clear(self) -> None:
        await self._conn.execute("DELETE FROM event;")
