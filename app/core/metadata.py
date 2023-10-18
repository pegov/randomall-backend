from pydantic import BaseModel


class Metadata(BaseModel):
    variations: int = 1
    hash: str = ""
