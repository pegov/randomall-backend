from enum import Enum
from typing import Optional, Type

from app.models.common import DefaultModel


class Kind(Enum):
    PERM = "perm"
    TEMP = "temp"


class Action(Enum):
    SET = "set"
    DELETE = "delete"


class ValueType(Enum):
    INT = "int"
    STR = "str"
    BOOL = "bool"


class ChangeSetting(DefaultModel):
    kind: Kind  # temp, direct
    action: Action  # set, delete
    section: str
    name: str
    type: Optional[ValueType] = None
    i_value: Optional[int] = None
    s_value: Optional[str] = None
    b_value: Optional[bool] = None
    ex: Optional[int] = None  # if kind == "temp" and action == "set"

    def value(self) -> int | str | bool:
        value_type = self.value_type()
        if value_type is int:
            return self.i_value  # type: ignore
        elif value_type is bool:
            return self.b_value  # type: ignore
        elif value_type is str:
            return self.s_value  # type: ignore
        else:
            raise Exception("Unreachable code")

    def value_type(self) -> Type[int | str | bool]:  # type: ignore
        if self.type is ValueType.INT:
            return int
        elif self.type is ValueType.STR:
            return str
        elif self.type is ValueType.BOOL:
            return bool
