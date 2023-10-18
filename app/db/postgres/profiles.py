from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from asyncpg import Connection
from sqlsl import Queries

from app.db.postgres.common import fix_user_field


class ProfileQ(Queries):
    get_gens_for_owner: str
    get_lists_for_owner: str
    get_gens_for_guest: str
    get_lists_for_guest: str
    get_gens_fav: str

    create_notification: str


path = Path(__file__).parent / "sql" / "profile.sql"
q = ProfileQ().from_file(path)


class ProfilesExt:
    def __init__(self, conn: Connection) -> None:
        self._conn = conn

    async def get(self, user_id: int) -> dict:
        description = await self._conn.fetchval(
            "SELECT description FROM profile_info WHERE user_id = $1;", user_id
        )
        return {
            "description": description,
        }

    async def update_description(self, user_id: int, description: str) -> None:
        if (
            await self._conn.fetchrow(
                "SELECT * FROM profile_info WHERE user_id = $1;",
                user_id,
            )
            is None
        ):
            await self._conn.execute(
                "INSERT INTO profile_info (user_id, description) VALUES ($1, $2);",
                user_id,
                description,
            )
        else:
            await self._conn.execute(
                "UPDATE profile_info SET description = $2 WHERE user_id = $1;",
                user_id,
                description,
            )

    async def get_gens_for_owner(self, user_id: int) -> List[dict]:
        return fix_user_field(await self._conn.fetch(q.get_gens_for_owner, user_id))

    async def get_lists_for_owner(self, user_id: int) -> List[dict]:
        return fix_user_field(await self._conn.fetch(q.get_lists_for_owner, user_id))

    async def get_gens_for_guest(self, user_id: int) -> List[dict]:
        return fix_user_field(await self._conn.fetch(q.get_gens_for_guest, user_id))

    async def get_lists_for_guest(self, user_id: int) -> List[dict]:
        return fix_user_field(await self._conn.fetch(q.get_lists_for_guest, user_id))

    async def get_gens_fav(self, user_id: int) -> List[dict]:
        return fix_user_field(await self._conn.fetch(q.get_gens_fav, user_id))

    async def create_notification(self, user_id: int, message: str) -> None:
        d = datetime.now(tz=timezone.utc)
        await self._conn.execute(
            q.create_notification,
            user_id,
            message,
            d,
        )

    async def get_notifications(self, user_id: int) -> List[dict]:
        return await self._conn.fetch(
            "SELECT * FROM profile_notification WHERE user_id = $1;", user_id
        )

    async def see_notifications(self, user_id: int) -> None:
        await self._conn.execute(
            "UPDATE profile_notification SET seen = True WHERE user_id = $1;",
            user_id,
        )

    async def get_global_access_key(self, user_id: int) -> Optional[str]:
        return await self._conn.fetchval(
            "SELECT global_access_key FROM profile_dev WHERE user_id = $1;",
            user_id,
        )

    async def set_global_access_key(self, user_id: int, key: str) -> None:
        async with self._conn.transaction():
            if (
                await self._conn.fetchrow(
                    "SELECT * FROM profile_dev WHERE user_id = $1;", user_id
                )
                is None
            ):
                await self._conn.execute(
                    "INSERT INTO profile_dev(user_id, global_access_key) VALUES ($1, $2);",
                    user_id,
                    key,
                )
            else:
                await self._conn.execute(
                    "UPDATE profile_dev SET global_access_key = $2 WHERE user_id = $1;",
                    user_id,
                    key,
                )

    async def delete_global_access_key(self, user_id: int) -> None:
        await self._conn.execute(
            "UPDATE profile_dev SET global_access_key = NULL WHERE user_id = $1",
            user_id,
        )
