from typing import Any

from pydantic import BaseConfig, BaseModel


def convert_field_to_camel_case(string: str) -> str:
    return "".join(
        word if index == 0 else word.capitalize()
        for index, word in enumerate(string.split("_"))
    )


class DefaultModel(BaseModel):
    class Config(BaseConfig):
        allow_population_by_field_name = True
        alias_generator = convert_field_to_camel_case

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)


class User(DefaultModel):
    id: int
    username: str


class RecursiveConstructModel(BaseModel):
    @classmethod
    def construct(cls, _fields_set=None, **values):

        m = cls.__new__(cls)
        fields_values = {}

        for name, field in cls.__fields__.items():
            key = field.alias
            if key in values:  # this check is necessary or Optional fields will crash
                try:
                    # if issubclass(field.type_, BaseModel):  # this is cleaner but slower
                    if field.shape == 2:
                        fields_values[name] = [
                            field.type_.construct(**e) for e in values[key]
                        ]
                    else:
                        fields_values[name] = field.outer_type_.construct(**values[key])
                except AttributeError:
                    if values[key] is None and not field.required:
                        fields_values[name] = field.get_default()
                    else:
                        fields_values[name] = values[key]
            elif not field.required:
                fields_values[name] = field.get_default()

        object.__setattr__(m, "__dict__", fields_values)
        if _fields_set is None:
            _fields_set = set(values.keys())
        object.__setattr__(m, "__fields_set__", _fields_set)
        m._init_private_attributes()
        return m
