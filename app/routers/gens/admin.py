from typing import List

from fastapi import APIRouter, Depends, HTTPException
from fastapi_auth import admin_required

from app.models.gens import Ping, RenameSubcategory, RenameTag, Stats
from app.repo.gens import GensRepo
from app.routers.dependencies import get_gens_repo as get_repo

router = APIRouter(
    dependencies=[Depends(admin_required)],
)


@router.get(
    "/ping",
    name="gens:get_pings",
    response_model=List[Ping],
)
async def gens_get_pings(
    repo: GensRepo = Depends(get_repo),
):
    return await repo.get_pings()


@router.get(
    "/stats",
    name="gens:get_stats",
    response_model=Stats,
)
async def gens_get_stats(
    repo: GensRepo = Depends(get_repo),
):
    return await repo.get_stats()


@router.post(
    "/tags/rename",
    name="gens:rename_tag",
)
async def gens_rename_tag(
    data_in: RenameTag,
    repo: GensRepo = Depends(get_repo),
):
    if not await repo.rename_tag(data_in.old, data_in.new):
        raise HTTPException(400, detail="name already exists")


@router.post(
    "/categories/rename_subcategory",
    name="gens:rename_subcategory",
)
async def gens_rename_subcategory(
    data_in: RenameSubcategory,
    repo: GensRepo = Depends(get_repo),
):
    if not await repo.rename_subcategory(data_in.category, data_in.old, data_in.new):
        raise HTTPException(400, detail="name already exists")
