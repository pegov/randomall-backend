from typing import List

from fastapi import APIRouter, Depends
from fastapi_auth import User, get_authenticated_user

from app.models.users import Notification
from app.repo.users import UsersRepo
from app.routers.dependencies import get_users_repo as get_repo

router = APIRouter()


@router.get(
    "/notifications",
    name="users:get_notifications",
    response_model=List[Notification],
)
async def profiles_get_notifications(
    repo: UsersRepo = Depends(get_repo),
    user: User = Depends(get_authenticated_user),
):
    return await repo.get_notifications(user.id)  # type: ignore


@router.post(
    "/notifications",
    name="users:see_notifications",
)
async def profiles_see_notifications(
    repo: UsersRepo = Depends(get_repo),
    user: User = Depends(get_authenticated_user),
):
    await repo.see_notifications(user.id)  # type: ignore
