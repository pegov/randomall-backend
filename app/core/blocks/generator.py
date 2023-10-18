import copy
import random
from typing import Any, List

from pydantic import ValidationError

from app.core.abc import AbstractGenerator
from app.core.blocks.body import Block, Body
from app.core.blocks.errors import (
    BlocksEngineValidationError,
    BlocksFormatValidationError,
)
from app.core.blocks.format import Format
from app.core.blocks.middlewares.backup import BackupMiddleware
from app.core.blocks.middlewares.hash import HashMiddleware
from app.core.blocks.middlewares.list import ListMiddleware
from app.core.blocks.middlewares.multiply import MultiplyMiddleware
from app.core.blocks.middlewares.num import NumMiddleware
from app.core.blocks.middlewares.variations import VariationsMiddleware
from app.core.blocks.validator import BodyValidation, FormatValidation


def _split_content(blocks: List[Any]) -> None:
    for block in blocks:
        if block.vars:
            block.content = [c.strip() for c in block.content.split(block.slicer)]


def _resolve_end(end: int) -> str:
    symbols = [
        "",  # 1
        " ",  # 2
        ".",  # 3
        "\n",  # 4
        ", ",  # 5
        ". ",  # 6
        ".\n",  # 7
        "\n\n",  # 8
    ]
    return symbols[end - 1]


def _tie(block: Block, choice: str) -> str:
    end = _resolve_end(block.end)
    return f"{block.before}{choice}{block.after}{end}"


def _choose(block: Block) -> str:
    """
    https://bugs.python.org/issue38881
        if all weights are 0:
        for python 3.9 random.choices raises ValueError
        for python 3.8 random.choices returns last element
    """
    if not block.vars:
        return block.content

    # multi is from PreproccessorMiddleware multiply
    if not block.multi:
        try:
            choice = random.choice(block.content)
        except IndexError:
            choice = ""
    else:
        try:
            # if all(v == 0 for v in block.weights):  # type: ignore
            #     return ""
            choice = random.choices(block.content, weights=block.weights, k=1)[0]  # type: ignore
        except (ValueError, IndexError):
            return ""
    if block.cap:
        if len(choice) > 0:
            return choice[:1].upper() + choice[1:]
        else:
            return ""
    else:
        return choice


def _choose_and_cap(block: Block) -> str:
    choice = _choose(block)
    if block.cap:
        if len(choice) > 0:
            return choice[:1].upper() + choice[1:]
        else:
            return ""

    return choice


class BaseGenerator:
    def __init__(self, body: Body) -> None:
        self._body = body

    def generate(self) -> str:
        results = []
        for block in self._body.blocks:
            choice = _choose_and_cap(block)
            tied_choice = _tie(block, choice)
            results.append(tied_choice)

        return "".join(results)

    def test(self) -> str:
        return self.generate()


class SequencesGenerator(BaseGenerator):
    def generate(self) -> str:
        chosen_sequence = random.choice(self._body.sequences)
        result = self._generate_from_sequence(chosen_sequence)

        return result

    def _generate_from_sequence(self, sequence: List[int]) -> str:
        results = []
        for s in sequence:
            choice = _choose_and_cap(self._body.blocks[s - 1])
            tied_choice = _tie(self._body.blocks[s - 1], choice)
            results.append(tied_choice)

        return "".join(results)

    def test(self) -> str:
        results = []

        for i, sequence in enumerate(self._body.sequences, 1):
            sequence_choices = self._generate_from_sequence(sequence)

            sequence_choices_str = "".join(sequence_choices)
            test_result = f"{i}. {sequence_choices_str}"

            results.append(test_result)

        return "\n".join(results)


class ExceptionsGenerator(BaseGenerator):
    def _delete_same(self, blocks: List[Block], choice: str, e: int) -> None:
        """NOTE: Mutates blocks!"""

        # blocks, "b", 2

        block = blocks[e - 1]  # ["b", "d", "e"]
        if not block.vars:  # TODO: test
            return

        indexes_to_remove = []
        # TODO: case insensitive to tutorial
        if len(choice) > 0:
            w = choice.lower()
        else:
            w = ""

        low_content = [v.lower() for v in copy.deepcopy(block.content)]

        for i, v in enumerate(low_content):
            if v == w:
                indexes_to_remove.append(i)

        if block.multi:
            block.weights = [  # type: ignore
                weight if i not in indexes_to_remove else 0
                for i, weight in enumerate(block.weights)  # type: ignore
            ]
        else:
            block.content = [  # type: ignore
                v for i, v in enumerate(block.content) if i not in indexes_to_remove
            ]

    def generate(self):
        blocks = self._body.blocks
        exceptions = self._body.exceptions
        results = []

        # blocks = [["a", "b", "c"], ["b", "d", "e"]]
        # exceptions = [[1, 2]]
        # NOTE: "b" in both

        for i, block in enumerate(blocks, 1):
            # i_1 = 1
            # block_1 = ["a", "b", "c"]

            # i_2 = 2
            # block_2 = ["d", "e"]

            exceptions_copy = copy.deepcopy(exceptions)  # [[1, 2]]

            choice = _choose_and_cap(block)  # ["b"]
            tied_choice = _tie(block, choice)

            results.append(tied_choice)

            for exception in exceptions_copy:
                # exception_1 = [1, 2]
                if i in exception:  # 1 in [1,2] - True
                    exception.remove(i)  # [2]
                    for e in exception:
                        self._delete_same(blocks, choice, e)  # blocks, "b", 2

        return "".join(results)


class AdvancedGenerator(ExceptionsGenerator):
    def generate(self) -> str:
        sequences = self._body.sequences
        exceptions = self._body.exceptions

        results = []

        sequence = random.choice(sequences)
        # blocks = copy.deepcopy(self._data.blocks)
        blocks = self._body.blocks
        for s in sequence:
            choice = _choose_and_cap(blocks[s - 1])
            for exception in exceptions:
                if s in exception:
                    exception.remove(s)
                    for e in exception:
                        self._delete_same(blocks, choice, e)

            tied_choice = _tie(blocks[s - 1], choice)
            results.append(tied_choice)
        return "".join(results)

    def test(self) -> str:
        sequences = self._body.sequences
        exceptions = self._body.exceptions

        results = []
        for i, sequence in enumerate(sequences, 1):
            blocks = copy.deepcopy(self._body.blocks)  # a, b*10, c*50, d*200, d*300
            sequence_result = [f"{i}. "]
            for s in sequence:  # 1, 1, 1, 1
                exceptions_copy = copy.deepcopy(exceptions)
                choice = _choose_and_cap(blocks[s - 1])
                for exception in exceptions_copy:
                    if s in exception:
                        exception.remove(s)
                        for e in exception:
                            self._delete_same(blocks, choice, e)

                tied_choice = _tie(blocks[s - 1], choice)
                sequence_result.append(tied_choice)
            results.append("".join(sequence_result))

        return "\n".join(results)


class Generator(AbstractGenerator):
    preprocess_middlewares = [
        ListMiddleware(),
        NumMiddleware(),
        MultiplyMiddleware(),
    ]
    postprocess_test_middlewares = [
        BackupMiddleware(),
    ]
    postprocess_save_middlewares = [
        BackupMiddleware(),
        HashMiddleware(),
        VariationsMiddleware(),
    ]

    def _get_generator(self, body: Body) -> BaseGenerator:
        has_sequences = len(body.sequences) > 0
        has_exceptions = len(body.exceptions) > 0

        if not has_sequences and not has_exceptions:
            return BaseGenerator(body)
        elif has_sequences and not has_exceptions:
            return SequencesGenerator(body)
        elif not has_sequences and has_exceptions:
            return ExceptionsGenerator(body)
        else:
            return AdvancedGenerator(body)

    def generate(self, body: Body) -> str:
        _split_content(body.blocks)
        return self._get_generator(body).generate()

    def test(self, body: Body) -> str:
        _split_content(body.blocks)
        return self._get_generator(body).test()

    def validate_format(self, data: dict) -> Format:
        validated_data = FormatValidation(**data).dict()
        return Format.construct(**validated_data)

    def validate_body(self, data: dict) -> Body:
        validated_data = BodyValidation(**data).dict()
        return Body.construct(**validated_data)

    def construct_body(self, data: dict) -> Body:
        return Body.construct(**data)

    def create_format_error(self, e: ValidationError):
        return BlocksFormatValidationError(e)

    def create_body_error(self, e: ValidationError):
        return BlocksEngineValidationError(e)
