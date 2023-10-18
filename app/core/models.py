from enum import Enum

from pydantic import BaseModel


class Action(str, Enum):
    CREATE = "create"
    EDIT = "edit"
    TEST = "test"
    GENERATE = "generate"


class Owner(BaseModel):
    id: int
    username: str
