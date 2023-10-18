from datetime import datetime
from typing import List, Optional

from pydantic import validator

from app.models.common import DefaultModel


class Notification(DefaultModel):
    message: str
    created_at: datetime
    seen: bool


class PublicInfo(DefaultModel):
    id: int
    username: str


class PrivateInfo(PublicInfo):
    email: str
    provider: Optional[str] = None

    roles: List[str]

    active: bool
    verified: bool

    created_at: datetime
    last_login: datetime


class Profile(DefaultModel):
    description: Optional[str] = None


class UpdateDescription(DefaultModel):
    description: str

    @validator("description")
    def check_description(cls, v) -> str:
        v = v.strip()
        # if v == "":
        #     raise ValueError("blank")

        if len(v) > 2000:
            raise ValueError("too long")

        return v


class ProfileGAK(DefaultModel):
    gak: Optional[str]
