from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi_auth import admin_required
from fastapi_auth.repo import Repo as AuthRepo

from app.models.users import PrivateInfo
from app.repo.users import UsersRepo
from app.routers.dependencies import get_fastapi_auth_repo
from app.routers.dependencies import get_users_repo as get_repo

router = APIRouter(dependencies=[Depends(admin_required)])


@router.post(
    "/{user_id}/notify",
    name="users:notify",
)
async def profiles_create_notification(
    user_id: int,
    message: str = Body(None, embed=True),
    repo: UsersRepo = Depends(get_repo),
):
    await repo.create_notification(user_id, message)


@router.get(
    "/{user_id}/private",
    name="users:get_user_private",
    response_model=PrivateInfo,
    response_model_exclude_none=True,
)
async def users_get_user_private(
    user_id: int,
    repo: AuthRepo = Depends(get_fastapi_auth_repo),
):
    user = await repo.get(user_id)
    if user is None:
        raise HTTPException(404)

    return user
