from typing import Optional

from fastapi import APIRouter, Depends
from fastapi_auth import User, get_user

from app.models.lists import Search, SearchParams
from app.repo.lists import ListsRepo
from app.repo.settings import SettingsRepo
from app.routers.dependencies import get_lists_repo as get_repo
from app.routers.dependencies import get_settings_repo
from app.services.lists import search

router = APIRouter()


@router.get("", name="lists:search", response_model=Search)
async def lists_search(
    *,
    repo: ListsRepo = Depends(get_repo),
    settings_repo: SettingsRepo = Depends(get_settings_repo),
    user: User = Depends(get_user),
    q: Optional[str] = None,
    p: Optional[str] = "1",
):
    search_params = SearchParams(q=q, p=p)
    return await search(repo, settings_repo, user, search_params)
