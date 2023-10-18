from typing import List

from fastapi import APIRouter, Depends
from fastapi_auth import User, get_user

from app.models.lists import Profile as ListsProfile
from app.repo.lists import ListsRepo
from app.routers.dependencies import get_lists_repo

router = APIRouter()


@router.get(
    "/{user_id}/lists",
    name="users:get_lists",
    response_model=List[ListsProfile],
)
async def users_get_lists(
    user_id: int,
    repo: ListsRepo = Depends(get_lists_repo),
    user: User = Depends(get_user),
):
    if user is not None and (
        (user.is_authenticated() and user.id == user_id) or user.is_admin()
    ):
        items = await repo.get_profile_for_owner(user_id)
    else:
        items = await repo.get_profile_for_guest(user_id)

    return items
