import asyncio
import html
from typing import Optional

from fastapi_auth import User
from pydantic import ValidationError

from app.core.abc import AbstractEngine
from app.core.blocks.body import Body
from app.core.blocks.generator import Generator as BlocksGenerator
from app.core.errors import HeadValidationError
from app.core.head import Head
from app.core.metadata import Metadata
from app.core.models import Action, Owner
from app.core.response import (
    ErrorResponse,
    GenerateResponse,
    Response,
    SaveResponse,
    TestResponse,
)
from app.entities.gens import GeneratorEntity
from app.logger import Logger
from app.repo.gens import GensRepo
from app.repo.lists import ListsRepo


class HornetEngine(AbstractEngine):
    """
    generate:
        - preprocess body (num, list, multiply)
        - update views
    test:
        - preprocess body
        - test and backup or error
    create:
        - prepare for create: hash, variations, access_key, date, social
        - repo.create
        - postprocess: log, backup
    edit:
        - prepare for update: hash, variations, date_updated
        - repo.update
        - postprocess: log, backup

    """

    head: Head
    body: Body
    action: Action

    def __init__(
        self,
        data: dict,
        gens_repo: GensRepo,
        lists_repo: ListsRepo,
        logger: Logger,
        editor: User,
        entity: Optional[GeneratorEntity] = None,
    ) -> None:
        self.data = data
        self.metadata = Metadata()
        self.misc = {}
        self.gens_repo = gens_repo
        self.lists_repo = lists_repo
        self.logger = logger
        self.editor = editor
        self.entity = entity
        if entity is None:
            self.owner = Owner(
                id=editor.id,  # type: ignore
                username=editor.username,
            )
        else:
            self.owner = Owner(
                id=entity.user.id,
                username=entity.user.username,
            )

        self._head_raw = data.get("head")
        self.body_raw = data.get("body")
        self.format_raw = data.get("format")
        self.engine_raw = data.get("engine", {})
        self.generator_raw = self.engine_raw.get("generator", "blocks")
        self.features_raw = self.engine_raw.get("features", [])

        self._generator = BlocksGenerator()

    def _validate_head(self, response: Response) -> None:
        try:
            self.head = Head(**self._head_raw)  # type: ignore
        except ValidationError as e:
            head_error = HeadValidationError(e)
            response.head_message = head_error.get_msg()

    def _validate_format(self, response: Response) -> None:
        try:
            self.format = self._generator.validate_format(self.format_raw)  # type: ignore
        except ValidationError as e:
            format_error = self._generator.create_format_error(e)
            response.format_message = format_error.get_msg()

    def _validate_body(self, response: Response):
        try:
            self.body = self._generator.validate_body(self.body_raw)  # type: ignore
        except ValidationError as e:
            body_error = self._generator.create_body_error(e)
            response.body_message = body_error.get_msg()

    def _construct_body(self):
        self.body = self._generator.construct_body(self.body_raw)  # type: ignore

    async def _process(self, middlewares, **kwargs) -> None:
        for middleware in middlewares:
            if asyncio.iscoroutinefunction(middleware.__call__):
                await middleware(self, **kwargs)
            else:
                middleware(self, **kwargs)

    async def _preprocess(self, **kwargs) -> None:
        await self._process(self._generator.preprocess_middlewares, **kwargs)

    async def _postprocess(self, **kwargs) -> None:
        await self._process(self._generator.postprocess_save_middlewares, **kwargs)

    async def generate(self, **kwargs) -> GenerateResponse:
        self.action = Action.GENERATE
        self._construct_body()

        await self._preprocess(**kwargs)

        result = self._generator.generate(self.body)
        escaped_result = html.escape(result)

        response = Response()
        response.result = escaped_result
        return response.generate()

    async def test(self, **kwargs) -> TestResponse | ErrorResponse:
        self.action = Action.TEST

        response = Response()

        self._validate_head(response)
        self._validate_format(response)
        self._validate_body(response)

        if response.has_blocking_error():
            return response.error()

        await self._process(self._generator.postprocess_test_middlewares, **kwargs)

        await self._preprocess(**kwargs)
        result = self._generator.test(self.body)
        escaped_result = html.escape(result)
        response.result = escaped_result

        if response.has_error():
            return response.error()

        return response.test()

    async def create(self, **kwargs) -> SaveResponse | ErrorResponse:
        self.action = Action.CREATE

        response = Response()
        self._validate_head(response)
        self._validate_format(response)
        self._validate_body(response)

        if response.has_error():
            return response.error()

        await self._postprocess(**kwargs)

        id = await self.gens_repo.create(
            editor=self.editor,
            head=self.head,
            format=self.format.dict(),
            body=self.body.dict(),
            metadata=self.metadata,
        )

        response.id = id
        return response.save()

    async def edit(
        self,
        **kwargs,
    ) -> SaveResponse | ErrorResponse:
        self.action = Action.EDIT

        response = Response()
        self._validate_head(response)
        self._validate_format(response)
        self._validate_body(response)

        if response.has_error():
            return response.error()

        await self._postprocess(**kwargs)

        id = self.entity.id  # type: ignore
        await self.gens_repo.update(
            id,
            editor=self.editor,
            head=self.head,
            format=self.format.dict(),
            body=self.body.dict(),
            metadata=self.metadata,
        )
        response.id = id
        return response.save()
