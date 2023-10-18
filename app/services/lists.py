from typing import List

from fastapi import HTTPException
from fastapi_auth import User

from app.config import LANGUAGE
from app.entities.lists import ListEntity
from app.models.lists import SearchParams
from app.repo.lists import ListsRepo
from app.repo.settings import SettingsRepo

from ..entities.settings import ListsSetting


async def search(
    repo: ListsRepo,
    settings_repo: SettingsRepo,
    user: User,
    search_params: SearchParams,
) -> dict:
    page_size = await settings_repo.get_perm_int(ListsSetting.SEARCH_PAGE_SIZE)
    items, count = await repo.search_and_count(
        search_params,
        page_size,
        user is not None and user.is_admin(),
    )

    div = count // page_size
    pages = div if count % page_size == 0 else div + 1

    return {
        "items": items,
        "pages": pages,
        "current_page": search_params.p,
    }


def humanize_error(errors) -> str:  # type: ignore
    for error in errors:  # pragma: no cover
        if "Error" in error.get("msg"):
            if LANGUAGE == "RU":
                return "Серверная ошибка, проверьте данные!"
            else:
                return "Server error! Check your data."

    return "\n".join(error.get("msg") for error in errors)


async def get_status(settings_repo: SettingsRepo) -> dict:
    p_save_ban_create = await settings_repo.get_perm_bool(
        ListsSetting.EDITOR_SAVE_BAN_CREATE  # type: ignore
    )
    p_captcha_create = await settings_repo.get_perm_bool(
        ListsSetting.EDITOR_CAPTCHA_CREATE  # type: ignore
    )
    p_save_ban_edit = await settings_repo.get_perm_bool(
        ListsSetting.EDITOR_SAVE_BAN_EDIT  # type: ignore
    )
    p_captcha_edit = await settings_repo.get_perm_bool(
        ListsSetting.EDITOR_CAPTCHA_EDIT  # type: ignore
    )
    (t_save_ban_create, _) = await settings_repo.get_temp(
        ListsSetting.EDITOR_SAVE_BAN_CREATE  # type: ignore
    )
    (t_captcha_create, _) = await settings_repo.get_temp(
        ListsSetting.EDITOR_CAPTCHA_CREATE  # type: ignore
    )
    (t_save_ban_edit, _) = await settings_repo.get_temp(
        ListsSetting.EDITOR_SAVE_BAN_EDIT  # type: ignore
    )
    (t_captcha_edit, _) = await settings_repo.get_temp(
        ListsSetting.EDITOR_CAPTCHA_EDIT,  # type: ignore
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
    }


async def get_profile(
    repo: ListsRepo,
    user: User,
    user_id: int,
) -> List[dict]:
    if user_id == user.id or user.is_admin():
        items = await repo.get_profile_for_owner(user_id)
    else:
        items = await repo.get_profile_for_guest(user_id)
    return items


async def get_info(repo: ListsRepo, user: User, id: int) -> ListEntity:
    entity = await repo.get(id)
    if entity is None:
        raise HTTPException(404)

    entity.check_view_permissions(user)

    return entity


async def delete(
    repo: ListsRepo,
    user: User,
    id: int,
) -> None:
    entity = await repo.get(id)
    if entity is None:
        raise HTTPException(404)

    entity.check_edit_permissions(user)

    await repo.deactivate(id)


async def get_edit_info(
    repo: ListsRepo,
    user: User,
    id: int,
) -> ListEntity:
    entity = await repo.get(id)
    if entity is None:
        raise HTTPException(404)

    entity.check_edit_permissions(user)

    return entity
