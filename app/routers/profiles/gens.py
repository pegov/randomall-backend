from typing import List

from fastapi import APIRouter, Depends
from fastapi_auth import User, get_authenticated_user, get_user

from app.models.gens import Profile as GensProfile
from app.models.users import ProfileGAK
from app.repo.gens import GensRepo
from app.repo.users import UsersRepo
from app.routers.dependencies import get_gens_repo, get_users_repo
from app.utils.strings import create_random_string

router = APIRouter()


@router.get(
    "/me/gens/favs",
    name="users:get_gens_favs",
    response_model=List[GensProfile],
)
async def users_get_gens_favs(
    user: User = Depends(get_authenticated_user),
    repo: GensRepo = Depends(get_gens_repo),
):
    return await repo.get_profile_favs(user.id)  # type: ignore


@router.get(
    "/me/gens/dev/global_access_key",
    name="users:get_global_access_key",
    response_model=ProfileGAK,
)
async def users_get_global_access_key(
    user: User = Depends(get_authenticated_user),
    users_repo: UsersRepo = Depends(get_users_repo),
):
    gak = await users_repo.get_global_access_key(user.id)
    return ProfileGAK(gak=gak)


@router.put(
    "/me/gens/dev/global_access_key",
    name="users:set_global_access_key",
    response_model=ProfileGAK,
)
async def users_set_global_access_key(
    user: User = Depends(get_authenticated_user),
    users_repo: UsersRepo = Depends(get_users_repo),
):
    version = "v1"
    key = create_random_string(32)
    gak = f"{version}:{user.id}:{key}"
    await users_repo.set_global_access_key(
        user.id,
        gak,
    )
    return ProfileGAK(gak=gak)


@router.delete(
    "/me/gens/dev/global_access_key",
    name="users:delete_global_access_key",
    response_model=List[GensProfile],
)
async def users_delete_global_access_key(
    user: User = Depends(get_authenticated_user),
    users_repo: UsersRepo = Depends(get_users_repo),
):
    await users_repo.delete_global_access_key(user.id)


@router.get(
    "/{user_id}/gens",
    name="users:get_gens",
    response_model=List[GensProfile],
)
async def users_get_gens(
    user_id: int,
    repo: GensRepo = Depends(get_gens_repo),
    user: User = Depends(get_user),
):
    if user is not None and (
        (user.is_authenticated() and user.id == user_id) or user.is_admin()
    ):
        items = await repo.get_profile_for_owner(user_id)
    else:
        items = await repo.get_profile_for_guest(user_id)

    return items
