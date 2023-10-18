from fastapi import APIRouter, Depends
from fastapi_auth import admin_required

from app.models.general import WP, UncheckWPRequest, WPCheck, WPCount
from app.repo.general import GeneralRepo
from app.routers.dependencies import get_general_repo as get_repo

router = APIRouter(dependencies=[Depends(admin_required)])


@router.get(
    "/usergen/wp",
    name="general:get_first_unchecked_wp",
    response_model=WP,
)
async def general_get_first_unchecked_wp(
    repo: GeneralRepo = Depends(get_repo),
):
    return await repo.get_first_unchecked_wp()


@router.post(
    "/usergen/wp",
    name="general:check_wp",
)
async def general_check_wp(wp: WPCheck, repo: GeneralRepo = Depends(get_repo)):
    await repo.check_wp(wp.dict())


@router.get(
    "/usergen/wp/count",
    name="general:get_wp_count",
    response_model=WPCount,
)
async def general_get_wp_count(
    repo: GeneralRepo = Depends(get_repo),
):
    count = await repo.get_wp_count()
    return {"count": count}


@router.post(
    "/usergen/wp/uncheck",
    name="general:uncheck_wp",
)
async def general_uncheck_wp(
    data_in: UncheckWPRequest,
    repo: GeneralRepo = Depends(get_repo),
):
    await repo.uncheck_wp(data_in.id, data_in.valid)
