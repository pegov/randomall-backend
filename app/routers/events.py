from fastapi import APIRouter, Depends
from fastapi_auth import admin_required

from app.models.events import Search, SearchParams
from app.repo.events import EventsRepo
from app.routers.dependencies import get_events_repo

router = APIRouter(dependencies=[Depends(admin_required)])


@router.get(
    "",
    name="events:search",
    response_model=Search,
)
async def events_search(
    # sp: SearchParams,
    repo: EventsRepo = Depends(get_events_repo),
):
    sp = SearchParams()
    items, count, pages = await repo.search(sp)
    return Search.construct(
        items=items,
        count=count,
        pages=pages,
        current_page=sp.p,
    )


@router.post(
    "/clear",
    name="events:clear",
)
async def events_clear(
    repo: EventsRepo = Depends(get_events_repo),
):
    await repo.clear()


@router.delete(
    "/{id}",
    name="events:delete",
)
async def events_delete(
    id: int,
    repo: EventsRepo = Depends(get_events_repo),
):
    await repo.delete(id)
