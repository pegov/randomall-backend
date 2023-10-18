from typing import List

from pydantic import BaseModel, Extra

from app.models.common import RecursiveConstructModel


class Block(BaseModel):
    vars: bool
    before: str
    slicer: str
    content: str
    cap: bool
    after: str
    end: int

    multi: bool = False

    class Config:
        extra = Extra.allow


class Body(RecursiveConstructModel):
    blocks: List[Block]

    sequences: List[List[int]] = []
    exceptions: List[List[int]] = []
