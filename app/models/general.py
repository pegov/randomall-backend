from enum import Enum
from typing import List, Optional

from pydantic import BaseModel

from app.models.common import DefaultModel


class Suggestion(DefaultModel):
    name: str
    value: str
    valid: bool = False
    checked: bool = False

    class Config:
        anystr_strip_whitespace = True


class SuggestionRequest(DefaultModel):
    name: str
    value: str


class Category(str, Enum):
    basic = "basic"
    hero = "hero"
    world = "world"


class Info(DefaultModel):
    category: Category
    position: int
    name: str
    title: str
    description_mainpage: str
    description_generator: str
    meta_description: str
    meta_keywords: str
    usergen: bool

    checked_count: Optional[int] = None
    not_checked_count: Optional[int] = None


class UsergenRequest(DefaultModel):
    id: int
    name: str
    value: str
    valid: bool


class Similar(BaseModel):
    value: str
    valid: bool


class FirstUsergenResponse(DefaultModel):
    id: int
    name: str
    value: str
    similar: List[Similar]


class LastUsergenItem(DefaultModel):
    id: int
    name: str
    value: str
    valid: bool


class LastWPItem(DefaultModel):
    id: int
    value: str
    english: str
    valid: bool


class LastUsergen(DefaultModel):
    creative: List[LastUsergenItem]
    wp: List[LastWPItem]


class UsergenStats(DefaultModel):
    valid: dict
    unchecked: dict


class UsergenCount(DefaultModel):
    count: int


class UsergenStatusItem(DefaultModel):
    name: str
    title: str
    usergen: bool


class WP(DefaultModel):
    id: int
    name: str = "plot"
    value: str
    english: str


class WPCheck(WP):
    valid: bool


class WPCount(DefaultModel):
    count: int


class UncheckUsergenRequest(DefaultModel):
    id: int
    name: str
    valid: bool


class UncheckWPRequest(DefaultModel):
    id: int
    valid: bool
