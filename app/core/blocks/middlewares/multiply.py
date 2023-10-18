import re

from app.core.abc import AbstractEngine

MULTIPLY_PATTERN = re.compile(r"(.+)?\*(\d+)$")
MAX_WEIGHT = 10_000


class MultiplyMiddleware:
    def __call__(self, engine: AbstractEngine, **kwargs) -> None:
        for block in engine.body.blocks:
            if "*" not in block.content:
                continue

            variants = block.content.split(block.slicer)

            values: list[str] = []
            weights: list[int] = []
            is_multi = False
            for v in variants:
                match = re.match(MULTIPLY_PATTERN, v)
                if match is None:
                    weights.append(1)
                    values.append(v)
                    continue

                value = match.group(1)
                weight = int(match.group(2))

                if value is None:
                    value = ""

                if weight <= 0:
                    weight = 0

                if weight > MAX_WEIGHT:
                    weight = MAX_WEIGHT

                values.append(value)
                weights.append(weight)
                is_multi = True

            if is_multi:
                block.content = block.slicer.join(values)
                block.weights = weights  # type: ignore
                block.multi = True
