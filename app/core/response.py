from enum import Enum
from typing import Optional

from pydantic import BaseModel


class Status(str, Enum):
    SAVE = "save"
    TEST = "test"
    ERROR = "error"


class Error(BaseModel):
    head: Optional[dict] = None
    format: Optional[dict] = None
    body: Optional[dict] = None
    result: Optional[str] = None


class Result(BaseModel):
    result: str


class SaveId(BaseModel):
    id: int


class SaveResponse(BaseModel):
    status = Status.SAVE
    msg: SaveId


class TestResponse(BaseModel):
    status = Status.TEST
    msg: Result


class ErrorResponse(BaseModel):
    status = Status.ERROR
    msg: Error


class GenerateResponse(BaseModel):
    msg: str


class Response:
    head_message: Optional[dict]
    format_message: Optional[dict]
    body_message: Optional[dict]
    result: Optional[str]
    id: Optional[int]

    def __init__(self) -> None:
        self.head_message = None
        self.format_message = None
        self.body_message = None
        self.result = None

    def save(self) -> SaveResponse:
        assert self.id is not None
        return SaveResponse(msg=SaveId(id=self.id))

    def test(self) -> TestResponse:
        assert self.result is not None
        return TestResponse(msg=Result(result=self.result))

    def error(self):
        return ErrorResponse(
            msg=Error(
                head=self.head_message,
                format=self.format_message,
                body=self.body_message,
                result=self.result,
            )
        )

    def generate(self) -> GenerateResponse:
        assert self.result is not None
        return GenerateResponse(msg=self.result)

    def has_error(self) -> bool:
        return (
            self.head_message is not None
            or self.format_message is not None
            or self.body_message is not None
        )

    def has_blocking_error(self) -> bool:
        return self.body_message is not None
