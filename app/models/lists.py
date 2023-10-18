from typing import List, Optional, Union

from pydantic import Field, validator

from app.config import LANGUAGE
from app.models.common import DefaultModel, User

CONTENT_LIMIT_BYTES = 16_000


class SearchParams(DefaultModel):
    title: Optional[str] = Field(None, alias="q")
    p: int = 1

    @validator("title")
    def check_q(cls, v):
        if v and (isinstance(v, str) and v.strip() != ""):
            return v
        return None

    @validator("p", pre=True)
    def check_p(cls, v):
        if v is not None and v.isdigit():
            return v
        else:
            return 1


class PublicInfo(DefaultModel):
    user: User
    id: int

    title: str
    description: Optional[str] = None

    access: int
    active: bool


class Info(PublicInfo):
    slicer: int
    content: str


class Search(DefaultModel):
    items: List[PublicInfo]
    pages: int
    current_page: int


if LANGUAGE == "RU":
    WRONG_ACCESS = "Неверный доступ"
    TITLE_CANT_BE_BLANK = "Название не может быть пустым"
    TITLE_TOO_LONG = "Название не может быть таким большим"
    DESCRIPTION_TOO_LONG = "Описание не может быть таким большим"
    WRONG_SLICER = "Неверный разделитель"
    CONTENT_CANT_BE_BLANK = "Контент не может быть пустым"
    CONTENT_TOO_LONG = "Контент не может быть таким большим (не больше 16000 символов)"
else:
    WRONG_ACCESS = "Wrong access value"
    TITLE_CANT_BE_BLANK = "Title can't be blank"
    TITLE_TOO_LONG = "Title is too long"
    DESCRIPTION_TOO_LONG = "Description is too long"
    WRONG_SLICER = "Wrong slicer value"
    CONTENT_CANT_BE_BLANK = "Cotent can't be blank"
    CONTENT_TOO_LONG = "Content is too long (no more than 16000 symbols)"


class ListInSave(DefaultModel):
    title: str
    description: Optional[str] = None

    access: int

    slicer: int
    content: str

    active: bool = True

    @validator("access")
    def check_access(cls, v):
        if v == 0 or v == 1:
            return v
        else:
            raise ValueError(WRONG_ACCESS)

    @validator("title")
    def check_title(cls, v):
        if v == "":
            raise ValueError(TITLE_CANT_BE_BLANK)
        if len(v) > 256:
            raise ValueError(TITLE_TOO_LONG)
        return v

    @validator("description")
    def check_description(cls, v):
        if v is not None:
            v = v.strip()
            if len(v) > 1000:
                raise ValueError(DESCRIPTION_TOO_LONG)
        return v

    @validator("slicer")
    def check_slicer(cls, v):
        if v >= 0 and v <= 3:
            return v
        raise ValueError(WRONG_SLICER)

    @validator("content")
    def check_content(cls, v):
        v = v.strip()
        if len(v) == 0:
            raise ValueError(CONTENT_CANT_BE_BLANK)
        if len(v) == CONTENT_LIMIT_BYTES:
            raise ValueError(CONTENT_TOO_LONG)
        return v


class EditorResponse(DefaultModel):
    status: str
    msg: Union[str, dict]


class Stats(DefaultModel):
    active: int
    inactive: int
    public: int
    private: int


class Profile(DefaultModel):
    id: int
    user: User
    title: str
    description: Optional[str] = None
    access: int
    active: bool


class EditorStatus(DefaultModel):
    save_ban_create: bool
    save_ban_edit: bool
    captcha_create: bool
    captcha_edit: bool
