import asyncio
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi_auth import User, get_authenticated_user

from app.core.engine.hornet import HornetEngine
from app.core.response import Status
from app.detail import Detail
from app.entities.events import Event
from app.entities.settings import GensSetting
from app.logger import Logger, create_editor_log
from app.models.gens import VH, ChangeKey, EditorStatus, Session, VHShort
from app.repo.events import EventsRepo
from app.repo.gens import GensRepo
from app.repo.lists import ListsRepo
from app.repo.settings import SettingsRepo
from app.routers.dependencies import TelegramNotifier, get_events_repo
from app.routers.dependencies import get_gens_repo
from app.routers.dependencies import get_gens_repo as get_repo
from app.routers.dependencies import (
    get_lists_repo,
    get_logger,
    get_notifier,
    get_settings_repo,
)
from app.utils.captcha import is_captcha_valid
from app.utils.strings import create_random_string

router = APIRouter()


@router.post("", name="gens:create")
async def gens_create_new(
    *,
    gens_repo: GensRepo = Depends(get_repo),
    lists_repo: ListsRepo = Depends(get_lists_repo),
    settings_repo: SettingsRepo = Depends(get_settings_repo),
    events_repo: EventsRepo = Depends(get_events_repo),
    user: User = Depends(get_authenticated_user),
    logger: Logger = Depends(get_logger),
    notifier: TelegramNotifier = Depends(get_notifier),
    request: Request,
):
    p_save_ban_create = await settings_repo.get_perm_bool(
        GensSetting.EDITOR_SAVE_BAN_CREATE  # type: ignore
    )
    p_captcha_create = await settings_repo.get_perm_bool(
        GensSetting.EDITOR_CAPTCHA_CREATE  # type: ignore
    )

    p_captcha_limit = await settings_repo.get_perm_int(
        GensSetting.EDITOR_SPAM_CAPTCHA_LIMIT,
    )
    p_captcha_duration = await settings_repo.get_perm_int(
        GensSetting.EDITOR_SPAM_CAPTCHA_DURATION,
    )
    p_ban_limit = await settings_repo.get_perm_int(
        GensSetting.EDITOR_SPAM_BAN_LIMIT,
    )
    p_ban_duration = await settings_repo.get_perm_int(
        GensSetting.EDITOR_SPAM_BAN_DURATION,
    )

    (t_save_ban_create, _), (t_captcha_create, _) = await asyncio.gather(
        settings_repo.get_temp(GensSetting.EDITOR_SAVE_BAN_CREATE),  # type: ignore
        settings_repo.get_temp(GensSetting.EDITOR_CAPTCHA_CREATE),  # type: ignore
    )

    data = await request.json()
    captcha = data.get("captcha")
    session = data.get("session")

    if p_save_ban_create or t_save_ban_create:
        if (
            session is not None
            and await gens_repo.get_create_session(user.id, session) is not None
        ):
            pass
        else:
            raise HTTPException(400, detail=Detail.CREATION_IS_DISABLED)

    if (p_captcha_create or t_captcha_create) and not await is_captcha_valid(captcha):
        raise HTTPException(400, detail=Detail.INVALID_CAPTCHA)

    ev = Event.GENS_EDITOR_CREATE
    engine = HornetEngine(data, gens_repo, lists_repo, logger, user)

    try:
        response = await engine.create()
        if response.status == Status.SAVE:
            log = create_editor_log(ev, user, request.client.host, response.msg.id)  # type: ignore
            await events_repo.create(ev, log)
            if session is not None:
                await gens_repo.delete_create_session(user.id, session)

            rate = await gens_repo.get_editor_rate()
            if not t_captcha_create and rate > p_captcha_limit:
                await settings_repo.set_temp(
                    GensSetting.EDITOR_CAPTCHA_CREATE,
                    True,
                    p_captcha_duration,
                )
                await notifier.notify_on_captcha()

            if not t_save_ban_create and rate > p_ban_limit:
                await settings_repo.set_temp(
                    GensSetting.EDITOR_SAVE_BAN_CREATE,
                    True,
                    p_ban_duration,
                )
                await notifier.notify_on_ban()

        return response
    except Exception as e:
        logger.gens.error(ev, e)
        raise e


@router.post("/test", name="gens:test")
async def gens_test_new(
    *,
    gens_repo: GensRepo = Depends(get_repo),
    lists_repo: ListsRepo = Depends(get_lists_repo),
    user: User = Depends(get_authenticated_user),
    logger: Logger = Depends(get_logger),
    request: Request,
):
    data = await request.json()

    try:
        engine = HornetEngine(
            data,
            gens_repo,
            lists_repo,
            logger,
            user,
        )
        return await engine.test()
    except Exception as e:
        logger.gens.error(Event.GENS_EDITOR_TEST, e)
        raise e


@router.put("/{id}", name="gens:edit")
async def gens_edit_new(
    *,
    id: int,
    gens_repo: GensRepo = Depends(get_repo),
    lists_repo: ListsRepo = Depends(get_lists_repo),
    settings_repo: SettingsRepo = Depends(get_settings_repo),
    events_repo: EventsRepo = Depends(get_events_repo),
    user: User = Depends(get_authenticated_user),
    logger: Logger = Depends(get_logger),
    request: Request,
):
    p_save_ban_edit = await settings_repo.get_perm_bool(
        GensSetting.EDITOR_SAVE_BAN_EDIT  # type: ignore
    )
    p_captcha_edit = await settings_repo.get_perm_bool(
        GensSetting.EDITOR_CAPTCHA_EDIT  # type: ignore
    )
    (t_save_edit_ban, _), (t_capctcha_edit, _) = await asyncio.gather(
        settings_repo.get_temp(GensSetting.EDITOR_SAVE_BAN_EDIT),  # type: ignore
        settings_repo.get_temp(GensSetting.EDITOR_CAPTCHA_EDIT),  # type: ignore
    )

    data = await request.json()
    captcha = data.get("captcha")
    session = data.get("session")

    if p_save_ban_edit or t_save_edit_ban:
        if (
            session is not None
            and await gens_repo.get_edit_session(user.id, session) is not None
        ):
            pass
        raise HTTPException(400, detail=Detail.CREATION_IS_DISABLED)

    if (p_captcha_edit or t_capctcha_edit) and not await is_captcha_valid(captcha):
        raise HTTPException(400, detail=Detail.INVALID_CAPTCHA)

    entity = await gens_repo.get(id)
    if entity is None:
        raise HTTPException(404)

    entity.check_edit_permissions(user)

    ev = Event.GENS_EDITOR_EDIT
    try:
        engine = HornetEngine(data, gens_repo, lists_repo, logger, user, entity)

        response = await engine.edit()
        if response.status == Status.SAVE:
            gens_repo.reset_preview_in_background()

            log = create_editor_log(ev, user, request.client.host, entity.id)
            await events_repo.create(ev, log)

        return response

    except Exception as e:
        logger.gens.error(ev, e)
        raise e


@router.get(
    "/session/{action}",
    name="gens:new_session",
    response_model=Session,
)
async def gens_new_session(
    action: str,
    repo: GensRepo = Depends(get_gens_repo),
    settings_repo: SettingsRepo = Depends(get_settings_repo),
    user: User = Depends(get_authenticated_user),
):
    p_save_ban_create = await settings_repo.get_perm_bool(
        GensSetting.EDITOR_SAVE_BAN_CREATE,
    )
    p_save_ban_edit = await settings_repo.get_perm_bool(
        GensSetting.EDITOR_SAVE_BAN_EDIT,
    )
    t_save_ban_create, _ = await settings_repo.get_temp(
        GensSetting.EDITOR_SAVE_BAN_CREATE,
    )
    t_save_ban_edit, _ = await settings_repo.get_temp(
        GensSetting.EDITOR_SAVE_BAN_EDIT,
    )

    match action:
        case "create":
            if p_save_ban_create or t_save_ban_create:
                raise HTTPException(423)
            session = await repo.new_create_session(user.id)
        case "edit":
            if p_save_ban_edit or t_save_ban_edit:
                raise HTTPException(423)
            session = await repo.new_edit_session(user.id)
        case _:
            raise HTTPException(404)

    return {"session": session}


@router.delete(
    "/session/{action}",
    name="gens:delete_session",
)
async def gens_delete_session(
    action: str,
    data_in: Session,
    repo: GensRepo = Depends(get_gens_repo),
    user: User = Depends(get_authenticated_user),
):
    match action:
        case "create":
            await repo.delete_create_session(user.id, data_in.session)
        case "edit":
            await repo.delete_edit_session(user.id, data_in.session)


@router.get(
    "/status",
    name="gens:get_status",
    response_model=EditorStatus,
)
async def gens_status(
    settings_repo: SettingsRepo = Depends(get_settings_repo),
):
    p_save_ban_create = await settings_repo.get_perm_bool(
        GensSetting.EDITOR_SAVE_BAN_CREATE  # type: ignore
    )
    p_save_ban_edit = await settings_repo.get_perm_bool(
        GensSetting.EDITOR_SAVE_BAN_EDIT  # type: ignore
    )
    p_captcha_create = await settings_repo.get_perm_bool(
        GensSetting.EDITOR_CAPTCHA_CREATE  # type: ignore
    )
    p_captcha_edit = await settings_repo.get_perm_bool(
        GensSetting.EDITOR_CAPTCHA_EDIT  # type: ignore
    )
    ping_interval = await settings_repo.get_perm_int(
        GensSetting.EDITOR_PING_INTERVAL  # type: ignore
    )
    (
        (t_save_ban_create, _),
        (t_save_ban_edit, _),
        (t_captcha_create, _),
        (t_captcha_edit, _),
    ) = await asyncio.gather(
        settings_repo.get_temp(GensSetting.EDITOR_SAVE_BAN_CREATE),  # type: ignore
        settings_repo.get_temp(GensSetting.EDITOR_SAVE_BAN_EDIT),  # type: ignore
        settings_repo.get_temp(GensSetting.EDITOR_CAPTCHA_CREATE),  # type: ignore
        settings_repo.get_temp(GensSetting.EDITOR_CAPTCHA_EDIT),  # type: ignore
    )

    save_ban_create = p_save_ban_create or t_save_ban_create
    save_ban_edit = p_save_ban_edit or t_save_ban_edit
    captcha_create = p_captcha_create or t_captcha_create
    captcha_edit = p_captcha_edit or t_captcha_edit

    return {
        "save_ban_create": save_ban_create,
        "save_ban_edit": save_ban_edit,
        "captcha_create": captcha_create,
        "captcha_edit": captcha_edit,
        "ping_interval": ping_interval,
    }


@router.get(
    "/vh",
    name="gens:get_last_vh",
    response_model=List[VHShort],
)
async def gens_get_last_vh(
    *,
    repo: GensRepo = Depends(get_repo),
    user: User = Depends(get_authenticated_user),
):
    return await repo.get_all_vh(user.id)


@router.get(
    "/vh/{id}",
    name="gens:get_vh",
    response_model=VH,
)
async def gens_get_vh(
    *,
    id: int,
    repo: GensRepo = Depends(get_repo),
    user: User = Depends(get_authenticated_user),
):
    vh = await repo.get_vh(id)
    if vh is None:
        raise HTTPException(404)

    # TODO: entity maybe???
    user_id = vh.get("user").get("id")
    if user.id != user_id and not user.is_admin():
        raise HTTPException(403)

    return vh


@router.post("/{id}/ping", name="gens:ping")
async def gens_ping(
    *,
    id: int,
    repo: GensRepo = Depends(get_repo),
    settings_repo: SettingsRepo = Depends(get_settings_repo),
    user: User = Depends(get_authenticated_user),
):
    interval = await settings_repo.get_perm_int(
        GensSetting.EDITOR_PING_INTERVAL,  # type: ignore
    )
    await repo.ping(id, user.id, interval)


@router.delete("/{id}", name="gens:delete")
async def gens_delete(
    *,
    id: int,
    repo: GensRepo = Depends(get_repo),
    events_repo: EventsRepo = Depends(get_events_repo),
    user: User = Depends(get_authenticated_user),
    request: Request,
):
    entity = await repo.get(id)
    if entity is None:
        raise HTTPException(404)

    entity.check_edit_permissions(user)

    await repo.delete(id)
    await repo.reset_preview()

    ev = Event.GENS_EDITOR_DELETE
    log = create_editor_log(ev, user, request.client.host, entity.id)
    await events_repo.create(ev, log, user)


@router.get(
    "/{id}/edit",
    name="gens:get_edit_info",
    response_model=dict,  # TODO
)
async def gens_edit_info(
    *,
    id: int,
    repo: GensRepo = Depends(get_repo),
    user: User = Depends(get_authenticated_user),
):
    entity = await repo.get(id)
    if entity is None:
        raise HTTPException(404)

    entity.check_edit_permissions(user)

    return entity


@router.post(
    "/{id}/key",
    name="gens:change_key",
    response_model=ChangeKey,
)
async def gens_change_key(
    *,
    id: int,
    repo: GensRepo = Depends(get_repo),
    user: User = Depends(get_authenticated_user),
):
    entity = await repo.get(id)
    if entity is None:
        raise HTTPException(404)

    entity.check_edit_permissions(user)

    new_access_key = create_random_string(32)
    await repo.change_access_key(id, new_access_key)

    return {"access_key": new_access_key}
