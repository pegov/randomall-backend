from fastapi import APIRouter, Depends
from fastapi_auth import User, get_user

from app.models.lists import Info
from app.repo.lists import ListsRepo
from app.routers.dependencies import get_lists_repo as get_repo
from app.services.lists import get_info

router = APIRouter()


@router.get(
    "/{id}",
    name="lists:get_info",
    response_model=Info,
)
async def lists_info(
    *,
    id: int,
    repo: ListsRepo = Depends(get_repo),
    user: User = Depends(get_user),
):
    return await get_info(repo, user, id)
