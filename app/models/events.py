from datetime import datetime
from typing import List, Optional

from app.models.common import DefaultModel, User


class SearchParams(DefaultModel):
    user_id: Optional[int] = None
    names: Optional[List[str]] = None
    created_at: Optional[datetime] = None
    size: int = 40
    p: int = 1


class Item(DefaultModel):
    id: int
    name: str
    user: User
    data: dict
    created_at: datetime


class Search(DefaultModel):
    items: List[Item]
    count: int
    pages: int
    current_page: int
