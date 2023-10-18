from datetime import datetime
from typing import List, Optional

from fastapi import HTTPException
from fastapi_auth import User
from pydantic import BaseModel

from app.entities.common import Owner
from app.models.gens import Access, Feature, Generator


class GeneratorEntity(BaseModel):
    id: int
    user: Owner

    title: str
    description: str
    category: Optional[str] = None
    subcategories: Optional[List[str]] = None
    tags: List[str]

    access: int
    access_key: str

    generator: Generator
    features: List[Feature]
    format: dict
    body: dict

    variations: int
    hash: Optional[str] = None

    likes: List[int]
    likes_count: int
    favs: List[int]
    favs_count: int
    views: int

    date_added: datetime
    date_updated: datetime

    active: bool = True
    ads: bool = True
    copyright: bool = False

    def is_owner(self, user: Optional[User]) -> bool:
        return user is not None and self.user.id == user.id

    def is_active(self, user: Optional[User]) -> bool:
        return self.active or (user is not None and user.is_admin())

    def has_copyright(self) -> bool:
        # return self.copyright.status
        return bool(self.copyright)

    def _is_accessable(
        self,
        user: Optional[User],
        secret: Optional[str],
    ) -> bool:

        if self.access == Access.PUBLIC:
            return True

        if self.access == Access.PRIVATE:
            return self.is_owner(user)

        if self.access == Access.LINK:
            return self.is_owner(user) or self.access_key == secret

        return False

    def check_view_permissions(
        self,
        user: Optional[User],
        secret: Optional[str],
    ) -> None:
        if user is not None and user.is_admin():
            return

        if not self.is_active(user):
            raise HTTPException(404)

        if self.has_copyright() and not self.is_owner(user):
            raise HTTPException(423, detail="copyright")

        if not self._is_accessable(user, secret):
            raise HTTPException(403)

    def check_edit_permissions(self, user: Optional[User]) -> None:
        if user is not None and user.is_admin():
            return

        if not self.is_active(user):
            raise HTTPException(404)

        if not self.is_owner(user):
            raise HTTPException(403)
