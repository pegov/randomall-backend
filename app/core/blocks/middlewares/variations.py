import copy

from app.core.abc import AbstractEngine
from app.core.blocks.middlewares.list import ListMiddleware

MAX = 100_000


class VariationsMiddleware:
    async def __call__(self, engine: AbstractEngine, **kwargs) -> None:
        body_copy = copy.deepcopy(engine.body)
        list_middleware = ListMiddleware()
        await list_middleware(engine, **kwargs)
        variations = 1
        for block in engine.body.blocks:
            if block.vars:
                v = len(block.content.split(block.slicer))
                if v > 0:
                    variations *= v
            if variations >= MAX:
                variations = MAX + 1
                break

        engine.body = body_copy
        engine.metadata.variations = variations
