import copy
import re

from app.config import LANGUAGE
from app.core.abc import AbstractEngine
from app.entities.lists import ListAccess

FUNC_PATTERN = re.compile(r"(LIST\(([0-9]+)*\))$")


class ListMiddleware:
    async def __call__(self, engine: AbstractEngine, **kwargs) -> None:
        for block in engine.body.blocks:
            variants = [v.strip() for v in block.content.split(block.slicer)]
            variants_copy = copy.deepcopy(variants)
            for v in variants_copy:
                for match in re.findall(FUNC_PATTERN, v):
                    try:
                        id = int(match[1])
                        list_variants = await self.get_content(engine, id)
                        variants_copy.remove(match[0])
                        variants_copy.extend(list_variants)
                    except ValueError:
                        pass

            block.content = block.slicer.join(variants_copy)

    async def get_content(self, engine: AbstractEngine, id: int) -> list[str]:
        entity = await engine.lists_repo.get(id)
        if entity is None:
            if LANGUAGE == "RU":
                return [f"__LIST({id})_ОШИБКА_СПИСКА_НЕ_СУЩЕСТВУЕТ__"]
            else:
                return [f"__LIST({id})_LIST_DOES_NOT_EXIST__"]
        if not entity.is_active():
            if LANGUAGE == "RU":
                return [f"__LIST({id})_ОШИБКА_СПИСКА_НЕ_СУЩЕСТВУЕТ__"]
            else:
                return [f"__LIST({id})_DOES_NOT_EXIST__"]
        if entity.access != ListAccess.PUBLIC and entity.user.id != engine.owner.id:
            if LANGUAGE == "RU":
                return [f"__LIST({id})_ОШИБКА_НЕТ_ДОСТУПА__"]
            else:
                return [f"__LIST({id})_IS_PRIVATE__"]

        return entity.get_variants()
