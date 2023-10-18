from typing import List

from asyncpg import Connection


class InternalExt:
    def __init__(self, conn: Connection) -> None:
        self._conn = conn

    async def get_sitemap(self) -> List[dict]:
        return await self._conn.fetch(
            "SELECT id, date_updated FROM gen WHERE access = 0 AND active = true ORDER BY id ASC;"
        )
