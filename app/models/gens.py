from datetime import datetime
from enum import Enum, IntEnum
from typing import List, Optional, Union

from pydantic import BaseModel, Field, validator

from app.models.common import DefaultModel, User


class GeneratorCopyright(BaseModel):
    status: bool = False
    name: Optional[str] = None
    link: Optional[str] = None


class Access(IntEnum):
    PUBLIC = 0
    PRIVATE = 1
    LINK = 2


class Generator(str, Enum):
    BLOCKS = "blocks"
    GENMARK = "genmark"


class Feature(str, Enum):
    MULTIPLY = "multiply"
    NUM = "num"
    LIST = "list"


class CopyrightInfo(BaseModel):
    name: Optional[str] = None
    link: Optional[str] = None


class Align(str, Enum):
    CENTER = "center"
    LEFT = "left"
    RIGHT = "right"
    JUSTIFY = "justify"


class Format(BaseModel):
    align: Align


class Runtime(BaseModel):
    generator: Generator
    features: List[Feature]


###


class SearchSort(str, Enum):
    DATE_UPDATED = "date_updated"
    DATE_ADDED = "date_added"
    VIEWS = "views"
    LIKES = "likes_count"


class SearchParams(DefaultModel):
    category: Optional[str] = Field(None, alias="c")
    subcategories: Optional[List[str]] = Field(None, alias="sc")
    title: Optional[str] = Field(None, alias="q")
    sort: Optional[SearchSort] = Field(SearchSort.LIKES, alias="f")
    tags: Optional[List[str]] = Field(None, alias="t")
    p: int = 1

    @validator("category", "title", "sort")
    def check_single(cls, v):
        if v and (isinstance(v, str) and v.strip() != ""):
            return v
        return None

    @validator("sort")
    def check_f(cls, v):
        if v is None:
            return SearchSort.LIKES
        else:
            return v

    @validator("subcategories", "tags")
    def check_list(cls, v):
        if v is None:
            return None
        v = [item for item in v if item.strip() != ""]
        if len(v) > 0:
            return v
        else:
            return None

    @validator("p", pre=True)
    def check_p(cls, v):
        if v is not None:
            return v
        else:
            return 1


class Suggestion(DefaultModel):
    id: int
    title: str
    likes_count: int


class PublicInfo(DefaultModel):
    id: int
    user: User

    category: Optional[str] = None
    subcategories: Optional[List[str]] = None
    tags: List[str]

    title: str
    description: str
    access: int
    variations: Optional[Union[int, str]] = None

    likes_count: int
    favs_count: int
    views: int

    liked: bool = False
    faved: bool = False

    date_added: datetime
    date_updated: datetime

    ads: bool = True
    active: bool = True
    copyright: bool = False

    generator: Generator
    format: dict


class PrivateInfo(PublicInfo):
    access_key: str


class EditorInfo(PublicInfo):
    features: List[str]
    body: dict


class Search(DefaultModel):
    items: List[PublicInfo]
    pages: int
    current_page: int


"""
+==========+
|  EDITOR  |
+==========+
"""


class EditorResponse(BaseModel):
    status: str
    msg: dict


class Subcategory(BaseModel):
    name: str
    count: int


class Category(BaseModel):
    name: str
    count: Optional[int] = None
    subcategories: Optional[List[Subcategory]] = None


class Tag(BaseModel):
    name: str
    count: int


class PreviewCategory(BaseModel):
    name: str
    count: int


class Preview(BaseModel):
    categories: List[PreviewCategory]
    new: List[PublicInfo]


class Result(BaseModel):
    msg: str


class ChangeKey(DefaultModel):
    access_key: str


class Ping(DefaultModel):
    user_id: int
    gen_id: int


# ADMIN
class Stats(DefaultModel):
    active: int
    inactive: int
    public: int
    private: int
    partly: int


class Profile(DefaultModel):
    id: int
    user: User
    title: str
    access: int
    views: int
    active: bool
    likes_count: int
    favs_count: int


class EditorStatus(DefaultModel):
    save_ban_create: bool
    save_ban_edit: bool
    captcha_create: bool
    captcha_edit: bool
    ping_interval: int


class RenameSubcategory(BaseModel):
    category: str
    old: str
    new: str

    class Config:
        anystr_strip_whitespace = True


class RenameTag(BaseModel):
    old: str
    new: str

    class Config:
        anystr_strip_whitespace = True


class VHShort(DefaultModel):
    id: int
    gen_id: int
    title: str
    access: int

    created_at: datetime


class VH(DefaultModel):
    id: int
    gen_id: int
    user: User

    title: str
    description: str
    access: int

    category: Optional[str] = None
    subcategories: Optional[List[str]] = None
    tags: List[str]

    generator: str
    features: List[str]

    format: dict
    body: dict

    created_at: datetime


class Session(BaseModel):
    session: str
