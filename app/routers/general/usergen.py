from html import escape
from typing import List, Optional, Union

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import ORJSONResponse
from fastapi_auth import admin_required

from app.models.general import (
    FirstUsergenResponse,
    Info,
    LastUsergen,
    Suggestion,
    SuggestionRequest,
    UncheckUsergenRequest,
    UsergenCount,
    UsergenRequest,
    UsergenStats,
    UsergenStatusItem,
)
from app.repo.general import GeneralRepo
from app.routers.dependencies import get_general_repo as get_repo
from app.services.general import validate_usergen

router = APIRouter()


@router.get(
    "",
    name="general:get_all_info",
    response_model=List[Union[Info, UsergenStatusItem]],
)
async def general_get_all_info(
    repo: GeneralRepo = Depends(get_repo),
    usergen_only: Optional[str] = Query(None),
):
    res = await repo.get_all_info()
    if usergen_only is None or usergen_only.strip() != "1":
        return ORJSONResponse([Info(**item).dict(by_alias=True) for item in res])

    names = [
        "crowd",
        "character",
        "motivation",
        "features",
        "race",
        "plot",
        "awkward_moment",
        "unexpected_event",
        "bookname",
    ]
    return ORJSONResponse(
        [
            UsergenStatusItem(**item).dict(by_alias=True)
            for item in res
            if item.get("name") in names
        ]
    )


@router.get(
    "/usergen",
    name="general:get_first_unchecked_usergen",
    dependencies=[Depends(admin_required)],
    response_model=FirstUsergenResponse,
)
async def general_first_usergen(
    repo: GeneralRepo = Depends(get_repo),
):
    res = await repo.get_first_unchecked_usergen()
    if res is None:
        raise HTTPException(404)

    variant, similar = res
    variant.update({"similar": similar})
    return variant


@router.post(
    "/usergen",
    name="general:check_usergen",
    dependencies=[Depends(admin_required)],
)
async def general_check_usergen(
    usergen: UsergenRequest,
    repo: GeneralRepo = Depends(get_repo),
):
    await repo.check(usergen.dict())


@router.post(
    "/usergen/uncheck",
    name="general:uncheck_usergen",
    dependencies=[Depends(admin_required)],
)
async def general_uncheck_usergen(
    data_in: UncheckUsergenRequest,
    repo: GeneralRepo = Depends(get_repo),
):
    await repo.uncheck(data_in.name, data_in.id, data_in.valid)


@router.get(
    "/usergen/count",
    name="general:get_usergen_count",
    dependencies=[Depends(admin_required)],
    response_model=UsergenCount,
)
async def general_get_usergen_count(
    repo: GeneralRepo = Depends(get_repo),
):
    count = await repo.get_usergen_count()
    return {"count": count}


@router.get(
    "/usergen/stats",
    name="general:get_stats",
    dependencies=[Depends(admin_required)],
    response_model=UsergenStats,
)
async def general_stats(
    repo: GeneralRepo = Depends(get_repo),
):
    return await repo.get_stats()


@router.get(
    "/usergen/last",
    name="general:get_last_checked_usergen",
    dependencies=[Depends(admin_required)],
    response_model=LastUsergen,
    response_description="last 30 checked usergen and 15 wp",
)
async def general_get_last_checked_usergen(
    repo: GeneralRepo = Depends(get_repo),
):
    creative = await repo.get_last_checked_usergen(50)
    wp = await repo.get_last_checked_wp(15)
    return {
        "creative": creative,
        "wp": wp,
    }


@router.post("/usergen/suggest", name="general:suggest")
async def general_suggest(
    s: SuggestionRequest,
    repo: GeneralRepo = Depends(get_repo),
):
    suggestion = Suggestion(name=s.name, value=s.value)
    if not validate_usergen(suggestion.value):
        return

    suggestion.value = suggestion.value[0].capitalize() + suggestion.value[1:]
    suggestion.value = escape(suggestion.value)

    valid_names = [
        "crowd",
        "character",
        "motivation",
        "features",
        "race",
        "plot",
        "awkward_moment",
        "unexpected_event",
        "bookname",
    ]
    if suggestion.name not in valid_names:
        raise HTTPException(400, detail=f"wrong name {suggestion.name}")

    # NOTE: to make sure
    suggestion.valid = False
    suggestion.checked = False

    if await repo.has_same_usergen(
        suggestion.name, suggestion.value
    ):  # pragma: no cover
        raise HTTPException(400, detail="same usergen")

    await repo.create_usergen(suggestion.dict())


@router.post(
    "/usergen/{name_}/toggle",
    name="general:toggle",
    dependencies=[Depends(admin_required)],
)
async def general_toggle(
    name_: str,
    repo: GeneralRepo = Depends(get_repo),
):
    await repo.toggle_usergen(name_)
