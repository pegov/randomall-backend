from enum import IntEnum
from typing import List, Optional

from fastapi import HTTPException
from fastapi_auth import User
from pydantic import BaseModel

from app.entities.common import Owner

SLICERS = (",", "\n", ".", ";")


class ListAccess(IntEnum):
    PUBLIC = 0
    PRIVATE = 1


class ListEntity(BaseModel):
    id: int
    user: Owner

    title: str
    description: Optional[str] = ""

    access: ListAccess
    active: bool = True

    content: str
    slicer: int

    def is_owner(self, user: Optional[User]) -> bool:
        return user is not None and user.is_authenticated() and self.user.id == user.id

    def is_active(self) -> bool:
        return self.active

    def _is_accessable(self, user: Optional[User]) -> bool:
        if self.access == ListAccess.PUBLIC:
            return True

        if self.access == ListAccess.PRIVATE:
            return self.is_owner(user)

        return False

    def check_view_permissions(self, user: Optional[User]) -> None:
        if user is not None and user.is_admin():
            return

        if not self.is_active():
            raise HTTPException(404)

        if not self._is_accessable(user):
            raise HTTPException(403)

    def check_edit_permissions(self, user: Optional[User]) -> None:
        if user is not None and user.is_admin():
            return

        if not self.is_active():
            raise HTTPException(404)

        if not self.is_owner(user):
            raise HTTPException(403)

    def get_variants(self) -> List[str]:
        return [v.strip() for v in self.content.split(SLICERS[self.slicer])]
