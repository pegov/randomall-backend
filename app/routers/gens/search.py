import random
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import ORJSONResponse
from fastapi_auth import User, get_user

from app.entities.events import Event
from app.entities.settings import GensSetting
from app.models.gens import Category, Preview, Search, SearchParams, Suggestion, Tag
from app.repo.events import EventsRepo
from app.repo.gens import GensRepo
from app.repo.settings import SettingsRepo
from app.routers.dependencies import get_events_repo
from app.routers.dependencies import get_gens_repo as get_repo
from app.routers.dependencies import get_settings_repo

router = APIRouter()


@router.get(
    "",
    name="gens:search",
    response_model=Search,
)
async def gens_search(
    *,
    repo: GensRepo = Depends(get_repo),
    settings_repo: SettingsRepo = Depends(get_settings_repo),
    events_repo: EventsRepo = Depends(get_events_repo),
    user: User = Depends(get_user),
    c: Optional[str] = None,
    sc: Optional[List[str]] = Query(None),
    t: Optional[List[str]] = Query(None),
    q: Optional[str] = None,
    f: Optional[str] = None,
    p: Optional[int] = 1,
):
    # TODO: try catch
    # BUG: value not in sort values somehow???
    sp = SearchParams(
        c=c,
        sc=sc,
        t=t,
        q=q,
        f=f,
        p=p,
    )

    log = sp.dict(exclude_none=True)

    page_size = await settings_repo.get_perm_int(GensSetting.SEARCH_PAGE_SIZE)

    items, count = await repo.search_and_count(
        sp,
        page_size,
        user is not None and user.is_admin(),
    )
    log.update({"count": count})  # type: ignore

    div = count // page_size
    pages = div if count % page_size == 0 else div + 1

    if sp.p == 1 and (
        sp.category is not None
        or sp.subcategories is not None
        or sp.tags is not None
        or sp.title is not None
    ):
        await events_repo.create(Event.GENS_SEARCH, log)

    return ORJSONResponse(
        Search(
            items=items,
            pages=pages,
            current_page=sp.p,
        ).dict(by_alias=True)
    )


@router.get(
    "/categories",
    name="gens:get_categories",
    response_model=List[Category],
)
async def gens_categories(
    repo: GensRepo = Depends(get_repo),
):
    return await repo.get_categories_and_count()


@router.get(
    "/titles",
    name="gens:get_titles",
    response_model=List[str],
)
async def gens_titles(
    *,
    repo: GensRepo = Depends(get_repo),
):
    return await repo.get_titles()


@router.get(
    "/tags",
    name="gens:get_tags",
    response_model=List[Tag],
)
async def gens_tags(
    repo: GensRepo = Depends(get_repo),
):
    return await repo.get_sorted_public_tags_and_count()


@router.get(
    "/suggestions",
    name="gens:get_suggestions",
    response_model=List[Suggestion],
)
async def gens_suggestions(
    repo: GensRepo = Depends(get_repo),
    settings_repo: SettingsRepo = Depends(get_settings_repo),
):
    suggestions_likes_threshold = await settings_repo.get_perm_int(
        GensSetting.VIEW_SUGGESTIONS_LIKES_THRESHOLD
    )
    suggestions_count = await settings_repo.get_perm_int(
        GensSetting.VIEW_SUGGESTIONS_COUNT
    )
    items = await repo.get_suggestions(suggestions_likes_threshold)
    n = len(items)
    if n > suggestions_count:
        return random.sample(items, suggestions_count)
    return items


@router.get(
    "/preview",
    name="gens:get_preview",
    response_model=Preview,
)
async def gens_preview(
    repo: GensRepo = Depends(get_repo),
    settings_repo: SettingsRepo = Depends(get_settings_repo),
):
    categories_and_count = await repo.get_categories_and_count()

    preview_count = await settings_repo.get_perm_int(GensSetting.VIEW_PREVIEW_COUNT)
    new = await repo.get_new_public(preview_count)

    return {
        "categories": categories_and_count,
        "new": new,
    }
