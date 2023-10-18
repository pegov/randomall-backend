from typing import Optional

from fastapi import APIRouter, Depends, Request
from fastapi.responses import ORJSONResponse
from fastapi_auth import User, get_authenticated_user, get_user

from app.logger import Logger
from app.models.gens import Result
from app.repo.gens import GensRepo
from app.repo.lists import ListsRepo
from app.repo.settings import SettingsRepo
from app.routers.dependencies import get_gens_repo as get_repo
from app.routers.dependencies import get_lists_repo, get_logger, get_settings_repo
from app.services.gens import fav, get_info, get_result, like

router = APIRouter()


@router.get(
    "/{id}",
    name="gens:get_info",
)
async def gens_info(
    *,
    id: int,
    repo: GensRepo = Depends(get_repo),
    user: User = Depends(get_user),
):
    return await get_info(repo, user, id)


@router.post(
    "/{id}",
    name="gens:get_result",
    response_model=Result,
)
async def gens_result(
    *,
    id: int,
    gens_repo: GensRepo = Depends(get_repo),
    lists_repo: ListsRepo = Depends(get_lists_repo),
    settings_repo: SettingsRepo = Depends(get_settings_repo),
    user: Optional[User] = Depends(get_user),
    logger: Logger = Depends(get_logger),
    request: Request,
):
    return await get_result(
        logger,
        gens_repo,
        lists_repo,
        settings_repo,
        user,
        id,
        request.client.host,
    )


@router.post("/{id}/like", name="gens:like")
async def gens_like(
    *,
    id: int,
    repo: GensRepo = Depends(get_repo),
    user: User = Depends(get_authenticated_user),
):
    await like(repo, user, id)


@router.post("/{id}/fav", name="gens:fav")
async def gens_fav(
    *,
    id: int,
    repo: GensRepo = Depends(get_repo),
    user: User = Depends(get_authenticated_user),
):
    await fav(repo, user, id)


@router.get(
    "/{id}/{secret}",
    name="gens:get_info_secret",
)
async def gens_info_secret(
    *,
    id: int,
    secret: str,
    repo: GensRepo = Depends(get_repo),
    user: User = Depends(get_user),
):

    data = await get_info(repo, user, id, secret)
    return ORJSONResponse(data)


@router.post(
    "/{id}/{secret}",
    name="gens:get_result_secret",
    response_model=Result,
)
async def gens_result_secret(
    *,
    id: int,
    secret: str,
    gens_repo: GensRepo = Depends(get_repo),
    lists_repo: ListsRepo = Depends(get_lists_repo),
    settings_repo: SettingsRepo = Depends(get_settings_repo),
    user: Optional[User] = Depends(get_user),
    logger: Logger = Depends(get_logger),
    request: Request,
):
    return await get_result(
        logger,
        gens_repo,
        lists_repo,
        settings_repo,
        user,
        id,
        request.client.host,
        secret,
    )
