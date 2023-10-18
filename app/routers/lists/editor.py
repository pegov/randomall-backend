import asyncio

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi_auth import User, get_authenticated_user
from pydantic import ValidationError

from app.detail import Detail
from app.entities.events import Event
from app.entities.settings import ListsSetting
from app.logger import Logger, create_editor_log
from app.models.lists import EditorResponse, EditorStatus, Info, ListInSave
from app.repo.events import EventsRepo
from app.repo.lists import ListsRepo
from app.repo.settings import SettingsRepo
from app.routers.dependencies import get_events_repo
from app.routers.dependencies import get_lists_repo as get_repo
from app.routers.dependencies import get_logger, get_settings_repo
from app.services.lists import delete, get_edit_info, get_status, humanize_error
from app.utils.captcha import is_captcha_valid

router = APIRouter()


@router.post("", name="lists:create", response_model=EditorResponse)
async def lists_create(
    *,
    repo: ListsRepo = Depends(get_repo),
    settings_repo: SettingsRepo = Depends(get_settings_repo),
    events_repo: EventsRepo = Depends(get_events_repo),
    user: User = Depends(get_authenticated_user),
    request: Request,
):
    p_save_ban_create = await settings_repo.get_perm_bool(
        ListsSetting.EDITOR_SAVE_BAN_CREATE  # type: ignore
    )
    p_captcha_create = await settings_repo.get_perm_bool(
        ListsSetting.EDITOR_CAPTCHA_CREATE  # type: ignore
    )

    (t_save_create_ban, _), (t_captcha_create, _) = await asyncio.gather(
        settings_repo.get_temp(ListsSetting.EDITOR_SAVE_BAN_CREATE),  # type: ignore
        settings_repo.get_temp(ListsSetting.EDITOR_CAPTCHA_CREATE),  # type: ignore
    )

    if p_save_ban_create or t_save_create_ban:
        raise HTTPException(400, detail=Detail.CREATION_IS_DISABLED)

    data = await request.json()
    captcha = data.get("captcha")

    if (p_captcha_create or t_captcha_create) and not await is_captcha_valid(captcha):
        return {"status": "error", "msg": "Введите каптчу"}

    try:
        model_obj = ListInSave(**data)
        model_obj.active = True  # just in case
    except ValidationError as e:
        return {"status": "error", "msg": humanize_error(e.errors())}

    obj = model_obj.dict(exclude_none=True)

    id = await repo.create(user, obj)

    ev = Event.LISTS_EDITOR_CREATE
    log = create_editor_log(ev, user, request.client.host, id)
    await events_repo.create(ev, log, user)

    return {
        "status": "save",
        "msg": {
            "id": id,
        },
    }


@router.get(
    "/status",
    name="lists:get_status",
    response_model=EditorStatus,
)
async def lists_get_status(
    repo: SettingsRepo = Depends(get_settings_repo),
):
    return await get_status(repo)


@router.put(
    "/{id}",
    name="lists:edit",
    response_model=EditorResponse,
)
async def lists_edit(
    *,
    id: int,
    request: Request,
    repo: ListsRepo = Depends(get_repo),
    events_repo: EventsRepo = Depends(get_events_repo),
    settings_repo: SettingsRepo = Depends(get_settings_repo),
    user: User = Depends(get_authenticated_user),
    logger: Logger = Depends(get_logger),
):
    p_save_ban_edit = await settings_repo.get_perm_bool(
        ListsSetting.EDITOR_SAVE_BAN_EDIT  # type: ignore
    )
    p_captcha_edit = await settings_repo.get_perm_bool(
        ListsSetting.EDITOR_CAPTCHA_EDIT  # type: ignore
    )

    (t_save_ban_edit, _), (t_capctcha_edit, _) = await asyncio.gather(
        settings_repo.get_temp(ListsSetting.EDITOR_SAVE_BAN_EDIT),  # type: ignore
        settings_repo.get_temp(ListsSetting.EDITOR_CAPTCHA_EDIT),  # type: ignore
    )

    if p_save_ban_edit or t_save_ban_edit:
        raise HTTPException(400, detail=Detail.CREATION_IS_DISABLED)

    data = await request.json()
    captcha = data.get("captcha")

    if (p_captcha_edit or t_capctcha_edit) and not await is_captcha_valid(captcha):
        return {"status": "error", "msg": "Введите каптчу"}

    entity = await repo.get(id)

    if entity is None:
        raise HTTPException(404)

    entity.check_edit_permissions(user)

    try:
        model_obj = ListInSave(**data)
    except ValidationError as e:
        return {"status": "error", "msg": humanize_error(e.errors())}

    obj = model_obj.dict(exclude_none=True)

    await repo.update(id, user, obj)

    ev = Event.LISTS_EDITOR_EDIT
    log = create_editor_log(ev, user, request.client.host, entity.id)
    await events_repo.create(ev, log, user)

    return {
        "status": "save",
        "msg": {
            "id": id,
        },
    }


@router.delete("/{id}", name="lists:delete")
async def lists_delete(
    *,
    id: int,
    request: Request,
    repo: ListsRepo = Depends(get_repo),
    events_repo: EventsRepo = Depends(get_events_repo),
    user: User = Depends(get_authenticated_user),
):
    await delete(repo, user, id)

    ev = Event.LISTS_EDITOR_DELETE
    log = create_editor_log(ev, user, request.client.host, id)
    await events_repo.create(ev, log, user)


@router.get("/{id}/edit", response_model=Info)
async def lists_edit_info(
    *,
    id: int,
    repo: ListsRepo = Depends(get_repo),
    user: User = Depends(get_authenticated_user),
):
    return await get_edit_info(repo, user, id)
