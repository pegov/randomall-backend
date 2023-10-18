from pydantic import BaseModel


class Owner(BaseModel):
    id: int
    username: str
