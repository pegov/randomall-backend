from typing import Callable, Optional

from fastapi import HTTPException
from fastapi_auth import User

from app.core.engine.hornet import HornetEngine
from app.core.response import GenerateResponse
from app.entities.events import Event
from app.entities.settings import GensSetting
from app.logger import Logger
from app.models.gens import PrivateInfo, PublicInfo
from app.repo.gens import GensRepo
from app.repo.lists import ListsRepo
from app.repo.settings import SettingsRepo


def _aproximate_variations(vars: Optional[int]) -> str:  # pragma: no cover
    if not vars:
        return ""

    marks = [
        (10, "<"),
        (30, "<"),
        (50, "<"),
        (100, "<"),
        (200, "<"),
        (300, "<"),
        (400, "<"),
        (500, "<"),
        (800, "<"),
        (1000, "~"),
        (1500, "~"),
        (2000, "~"),
        (2500, "~"),
        (3000, "~"),
        (4000, "~"),
        (5000, "~"),
        (6000, "~"),
        (7000, "~"),
        (8000, "~"),
        (9000, "~"),
        (10_000, "~"),
        (15_000, "~"),
        (20_000, "~"),
        (30_000, "~"),
        (50_000, "~"),
        (100_000, "~"),
    ]

    if vars >= marks[-1][0]:
        return f">{str(marks[-1][0])}"

    for mark in marks:
        if vars < mark[0]:
            return f"{mark[1]}{str(mark[0])}"

    return ""


async def get_info(
    repo: GensRepo,
    user: Optional[User],
    id: int,
    secret: Optional[str] = None,
) -> dict:
    entity = await repo.get(id)
    if entity is None:
        raise HTTPException(404)

    entity.check_view_permissions(user, secret)

    extra = {}

    a_variations = _aproximate_variations(entity.variations)  # type: ignore

    if user is not None:
        liked = user.id in entity.likes
        faved = user.id in entity.favs
    else:
        liked = False
        faved = False

    extra.update({"liked": liked, "faved": faved})
    extra.update({"variations": a_variations})  # type: ignore

    repo.increment_views(id)

    data = entity.dict()
    data.update(extra)

    if (user is not None and user.is_admin()) or entity.is_owner(user):
        return PrivateInfo(**data).dict(by_alias=True)

    return PublicInfo(**data).dict(by_alias=True)


async def get_result(
    logger: Logger,
    gens_repo: GensRepo,
    lists_repo: ListsRepo,
    settings_repo: SettingsRepo,
    user: Optional[User],
    id: int,
    ip: str,
    secret: Optional[str] = None,
) -> GenerateResponse:
    if await gens_repo.in_ratelimit_ban(ip):
        raise HTTPException(429, detail="too many requests")

    ratelimit = await settings_repo.get_perm_int(
        GensSetting.VIEW_RESULT_RATELIMIT,  # type: ignore
    )
    if await gens_repo.ratelimit_exceeded(ip, ratelimit):
        log = {
            "ip": ip,
            "id": id,
        }
        logger.gens.event(Event.GENS_RESULT_RATELIMIT, log)
        raise HTTPException(429, detail="too many requests")

    entity = await gens_repo.get(id)
    if entity is None:
        raise HTTPException(404)

    entity.check_view_permissions(user, secret)

    engine = HornetEngine(
        entity.dict(),
        gens_repo,
        lists_repo,
        logger,
        None,  # type: ignore
        entity,
    )

    return await engine.generate()


async def _social_action(
    repo: GensRepo,
    id: int,
    user: User,
    method: Callable[[int, User], None],
) -> None:
    entity = await repo.get(id)
    if entity is None:
        raise HTTPException(404)

    entity.check_view_permissions(user, None)

    await method(id, user.id)  # type: ignore


async def like(repo: GensRepo, user: User, id: int) -> None:
    await _social_action(repo, id, user, repo.like)  # type: ignore


async def fav(repo: GensRepo, user: User, id: int) -> None:
    await _social_action(repo, id, user, repo.fav)  # type: ignore
