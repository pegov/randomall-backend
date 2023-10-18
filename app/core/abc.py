from abc import ABC, abstractmethod
from typing import Optional

from fastapi_auth import User
from pydantic import ValidationError

from app.core.blocks.body import Body
from app.core.head import Head
from app.core.metadata import Metadata
from app.core.models import Action, Owner
from app.entities.gens import GeneratorEntity
from app.logger import Logger
from app.repo.gens import GensRepo
from app.repo.lists import ListsRepo


class AbstractEngine(ABC):
    head: Head
    body: Body
    action: Action
    owner: Owner
    editor: User
    data: dict
    metadata: Metadata
    misc: dict

    gens_repo: GensRepo
    lists_repo: ListsRepo
    entity: Optional[GeneratorEntity]
    logger: Logger

    @abstractmethod
    async def test(self):
        raise NotImplementedError

    @abstractmethod
    async def generate(self):
        raise NotImplementedError

    @abstractmethod
    async def create(self):
        raise NotImplementedError

    @abstractmethod
    async def edit(self):
        raise NotImplementedError


class AbstractGenerator(ABC):
    @abstractmethod
    def validate_format(self, data: dict):
        raise NotImplementedError

    @abstractmethod
    def validate_body(self, data: dict):
        raise NotImplementedError

    @abstractmethod
    def construct_body(self, data: dict):
        raise NotImplementedError

    @abstractmethod
    def create_format_error(self, e: ValidationError):
        raise NotImplementedError

    @abstractmethod
    def create_body_error(self, e: ValidationError):
        raise NotImplementedError

    @abstractmethod
    def generate(self, body) -> str:
        raise NotImplementedError

    @abstractmethod
    def test(self, body) -> str:
        raise NotImplementedError
