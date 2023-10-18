import asyncio
from typing import List

from asyncpg import Connection

from app.db.postgres.events import EventsExt
from app.db.postgres.general import GeneralExt
from app.db.postgres.gens import GensExt
from app.db.postgres.internal import InternalExt
from app.db.postgres.lists import ListsExt
from app.db.postgres.profiles import ProfilesExt
from app.db.postgres.settings import SettingsExt


class PostgresDB:
    def __init__(self, conn: Connection) -> None:
        self._conn = conn
        self.background_tasks: List[asyncio.Task] = []

        self.gens = GensExt(conn)
        self.lists = ListsExt(conn)
        self.settings = SettingsExt(conn)
        self.profiles = ProfilesExt(conn)
        self.general = GeneralExt(conn)
        self.internal = InternalExt(conn)
        self.events = EventsExt(conn)

    def background(self, fut) -> None:
        task = asyncio.create_task(fut)
        self.background_tasks.append(task)
