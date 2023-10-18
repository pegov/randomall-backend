from fastapi import APIRouter, Depends, HTTPException
from fastapi_auth import User, get_authenticated_user
from fastapi_auth.repo import Repo as AuthRepo

from app.entities.events import Event
from app.models.users import Profile, UpdateDescription
from app.repo.events import EventsRepo
from app.repo.users import UsersRepo
from app.routers.dependencies import (
    get_events_repo,
    get_fastapi_auth_repo,
    get_users_repo,
)

router = APIRouter()


@router.get(
    "/{user_id}/profile",
    name="users:get_profile",
    response_model=Profile,
)
async def users_get_profile(
    user_id: int,
    repo: UsersRepo = Depends(get_users_repo),
    auth_repo: AuthRepo = Depends(get_fastapi_auth_repo),
):
    if await auth_repo.get(user_id) is None:
        raise HTTPException(404)

    return await repo.get_profile(user_id)


@router.put(
    "/{user_id}/profile/description",
    name="users:update_profile",
)
async def users_update_profile_description(
    user_id: int,
    data_in: UpdateDescription,
    auth_repo: AuthRepo = Depends(get_fastapi_auth_repo),
    repo: UsersRepo = Depends(get_users_repo),
    user: User = Depends(get_authenticated_user),
    events_repo: EventsRepo = Depends(get_events_repo),
):
    if await auth_repo.get(user_id) is None:
        raise HTTPException(404)

    if user.id != user_id and not user.is_admin():
        raise HTTPException(403)

    await repo.update_description(user.id, data_in.description)
    if not user.is_admin():
        await events_repo.create(
            Event.PROFILES_INFO_EDIT,
            data_in.dict(),
            user,
        )
