import orjson

from app.core.abc import AbstractEngine
from app.entities.events import Event

MAX_SIZE_IN_BYTES = 1_000_000 * 5  # 5 MB


class BackupMiddleware:
    async def __call__(self, engine: AbstractEngine, **kwargs) -> None:
        dump = orjson.dumps(engine.body_raw).decode("utf-8")  # type: ignore
        cur_size = len(dump)
        backup = await engine.gens_repo.get_backup(engine.owner.id)

        if (backup is None or backup != dump) and cur_size < MAX_SIZE_IN_BYTES:
            log = {
                "user_id": engine.owner.id,
                **engine.data,
            }
            engine.logger.gens.event(Event.GENS_EDITOR_BACKUP, log)
            await engine.gens_repo.create_backup(engine.owner.id, dump)
