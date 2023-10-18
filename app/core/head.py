from typing import List, Optional

from pydantic import BaseModel, PydanticValueError, validator

from app.config import LANGUAGE
from app.core.localization import t

if LANGUAGE == "RU":
    VALID_CATEGORIES = {
        "Оригинальные": True,
        "Ролевые игры": True,
        "Игры": True,
        "Аниме и манга": True,
        "Мультфильмы": True,
        "Фильмы": True,
        "Сериалы": True,
        "Книги": True,
        "Известные личности": True,
        "Другое": False,
    }
else:
    VALID_CATEGORIES = {
        "Original": True,
        "Roleplay": True,
        "Games": True,
        "Anime and manga": True,
        "Cartoons": True,
        "Movies": True,
        "TV shows": True,
        "Books": True,
        "Other": False,
    }


def upper_list(input_list: List[str]):
    # for i, item in enumerate(lst):
    #     lst[i] = item[:1].upper() + item[1:]
    # return lst
    return [v[:1].upper() + v[1:] for v in input_list]


def upper_string(s: str):
    try:
        s = s[:1].upper() + s[1:]
    except:  # noqa: E722
        pass
    return s


class HeadValidationError(PydanticValueError):
    def __init__(self, key: str, **ctx) -> None:
        self.code = key
        try:
            self.msg_template = t["head"]["errors"][key]  # type: ignore
        except KeyError:
            self.msg_template = t["SERVER_ERROR"]  # type: ignore


class Head(BaseModel):
    title: str
    description: str

    access: int

    category: Optional[str] = None
    subcategories: Optional[List[str]] = None
    tags: Optional[List[str]] = None

    @validator("title")
    def check_title(cls, v):
        v = v.strip()
        if v == "":
            raise HeadValidationError("title_blank")
        if len(v) > 256:
            raise HeadValidationError("title_too_long")
        return v

    @validator("description")
    def check_description(cls, v):
        v = v.strip()
        if v == "":
            raise HeadValidationError("description_blank")
        if len(v) > 1000:
            raise HeadValidationError("description_too_long")
        return v

    @validator("access")
    def check_access(cls, v):
        # v = v.strip()
        if v < 0 or v > 2:
            raise HeadValidationError("access_error")
        return v

    @validator("tags")
    def check_tags(cls, v, values):
        if v is None:
            raise HeadValidationError("tags_blank")
        if len(v) > 0:
            result = []
            for tag in v:
                tag = tag.strip()
                if "#" in tag:
                    tag = tag.replace("#", "")
                if tag != "" and tag not in result and tag:
                    tag = upper_string(tag)
                    result.append(tag)
            if len(result) > 15:
                raise HeadValidationError("tags_too_many")
            if len(result) > 0:
                return result
            else:
                raise HeadValidationError("tags_error")
        else:
            raise HeadValidationError("tags_blank")

    @validator("category")
    def check_category(cls, v, values):
        if values.get("access") > 0:
            return None
        if v is None:
            raise HeadValidationError("category_blank")
        if v not in VALID_CATEGORIES.keys() and values.get("access") == 0:
            raise HeadValidationError("category_error")
        return v

    @validator("subcategories")
    def check_subcategories(cls, v, values):
        if v is None:
            return None
        if values.get("access") > 0:
            return None
        c = values.get("category")
        if not VALID_CATEGORIES.get(c):
            return None

        v = [s.strip() for s in v if s is not None and s.strip() != ""]
        v = list(set(v))

        if len(v) > 10:
            raise HeadValidationError("subcategories_too_many")

        if len(v) == 0:
            return None

        v = upper_list(v)
        return v


class HeadValidator:
    @staticmethod
    def validate(data: dict) -> dict:
        return Head(**data).dict()
