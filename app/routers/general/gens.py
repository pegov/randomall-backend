from fastapi import APIRouter, Depends, HTTPException, Request

from app.entities.events import Event
from app.entities.settings import GeneralSetting
from app.general.resolver import resolve_generation
from app.logger import Logger
from app.models.general import Info
from app.repo.general import GeneralRepo
from app.repo.settings import SettingsRepo
from app.routers.dependencies import get_general_repo as get_repo
from app.routers.dependencies import get_logger, get_settings_repo

router = APIRouter()


@router.get(
    "/{name_}",
    name="general:get_info",
    response_model=Info,
    response_model_exclude_none=True,
)
async def general_info(
    name_: str,
    repo: GeneralRepo = Depends(get_repo),
):
    item = await repo.get_info(name_)
    if item is None:
        raise HTTPException(404)

    if name_ == "plot":
        extension = await repo.get_plot_count()
        item.update(extension)

    return item


@router.post(
    "/{name_}",
    name="general:get_result",
    response_model=str,
)
async def general_result(
    name_: str,
    request: Request,
    repo: GeneralRepo = Depends(get_repo),
    settings_repo: SettingsRepo = Depends(get_settings_repo),
    logger: Logger = Depends(get_logger),
):
    try:
        data = await request.json()
    except Exception:  # noqa
        data = None

    ip = request.client.host

    if await repo.in_ratelimit_ban(ip):
        raise HTTPException(429, detail="Too many requests")

    ratelimit = await settings_repo.get_perm_int(GeneralSetting.RESULT_RATELIMIT)

    if await repo.ratelimit_exceeded(ip, ratelimit):
        log = {
            "ip": ip,
            "name": name_,
        }
        logger.event(Event.GENERAL_RESULT_RATELIMIT, log)
        raise HTTPException(429, detail="Too many requests")

    # response is just a string
    res = await resolve_generation(repo, name_, data)
    if res is None:
        raise HTTPException(404)

    return res
