import random
import re

from app.core.abc import AbstractEngine

FUNC_PATTERN = re.compile(r"(?=NUM\()[^)]*\)")
NUMBERS_PATTERN = re.compile(r"-?\d+(?:\.|d+)?")
MAGIC_NUMBER = 1_000_000_000_000


class NumError(Exception):
    pass


def random_number(nums: list[int]) -> str:
    nums = [int(n) for n in nums]

    c = len(nums)

    if (
        c == 2
        and nums[0] < nums[1]
        and nums[0] < MAGIC_NUMBER
        and nums[1] < MAGIC_NUMBER
    ):
        return str(random.randint(nums[0], nums[1]))
    elif (
        c == 3
        and (nums[0] < nums[1] and nums[2] > 0)
        and nums[0] < MAGIC_NUMBER
        and nums[1] < MAGIC_NUMBER
        and nums[2] < MAGIC_NUMBER
    ):
        if nums[2] > nums[1]:
            return str(nums[0])

        steps = (nums[1] - nums[0]) // nums[2]
        p = random.randint(0, steps)
        return str(nums[0] + nums[2] * p)
    else:
        raise NumError


class NumMiddleware:
    def __call__(self, engine: AbstractEngine, **kwargs) -> None:
        for block in engine.body.blocks:
            for match in re.findall(FUNC_PATTERN, block.content):
                match = match.replace(" ", "")
                nums = [n for n in re.findall(NUMBERS_PATTERN, match)]
                try:
                    replacement = random_number(nums)
                except (ValueError, NumError):
                    replacement = f"__ERROR__{match}__ERROR__"
                    replacement = replacement.replace(",", "__COMMA__")

                block.content = re.sub(FUNC_PATTERN, replacement, block.content, 1)
