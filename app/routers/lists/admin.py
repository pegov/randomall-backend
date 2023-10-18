from fastapi import APIRouter, Depends
from fastapi_auth import admin_required

from app.models.lists import Stats
from app.repo.lists import ListsRepo
from app.routers.dependencies import get_lists_repo as get_repo

router = APIRouter(
    dependencies=[Depends(admin_required)],
)


@router.get(
    "/stats",
    name="lists:get_stats",
    response_model=Stats,
)
async def lists_get_stats(
    repo: ListsRepo = Depends(get_repo),
):
    return await repo.get_stats()
