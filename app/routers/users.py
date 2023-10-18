from fastapi import APIRouter, Depends, HTTPException
from fastapi_auth.errors import UserNotFoundError
from fastapi_auth.repo import Repo as AuthRepo

from app.models.users import PublicInfo
from app.routers.dependencies import get_fastapi_auth_repo

router = APIRouter()


@router.get(
    "/by/username/{username}",
    name="users_get_user_by_username",
    response_model=PublicInfo,
    response_model_exclude_none=True,
)
async def users_get_user_by_username(
    username: str,
    repo: AuthRepo = Depends(get_fastapi_auth_repo),
):
    try:
        user = await repo.get_by_username(username)
        if not user.active:
            raise HTTPException(404)

        return user

    except UserNotFoundError:
        raise HTTPException(404) from None


@router.get(
    "/{user_id}",
    name="users:get_user",
    response_model=PublicInfo,
    response_model_exclude_none=True,
)
async def users_get_user(
    user_id: int,
    repo: AuthRepo = Depends(get_fastapi_auth_repo),
):
    try:
        user = await repo.get(user_id)
        if not user.active:
            raise HTTPException(404)

        return user

    except UserNotFoundError:
        raise HTTPException(404) from None
