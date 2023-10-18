import re
from typing import List

from pydantic import BaseModel, PydanticValueError, validator

from app.core.localization import t

CONTENT_LIMIT_BYTES = 100_000
BEFORE_AFTER_LIMIT = 1_000


class ValidationError(PydanticValueError):
    def __init__(self, key: str, **ctx) -> None:
        self.code = key
        try:
            self.msg_template = t["body"]["blocks"]["errors"][key]  # type: ignore
        except KeyError:
            self.msg_template = t["SERVER_ERROR"]  # type: ignore


class ModValidationError(PydanticValueError):
    def __init__(self, key: str, **ctx) -> None:
        self.code = key
        try:
            self.msg_template = t["body"]["blocks"]["errors"][key].format(**ctx)  # type: ignore
        except Exception:
            self.msg_template = t["SERVER_ERROR"]  # type: ignore


class BlockValidation(BaseModel):
    vars: bool
    before: str
    after: str
    slicer: str
    content: str
    cap: bool
    end: int

    @validator("vars", "cap")
    def check_var(cls, v: bool) -> bool:
        return v

    @validator("before")
    def check_before(cls, v: str) -> str:
        if v is None or v.isspace():
            return ""
        if len(v) > BEFORE_AFTER_LIMIT:
            raise ValidationError("before_after_too_long")

        v = v.lstrip()

        return v

    @validator("after")
    def check_before_after(cls, v: str) -> str:
        if v is None or v.isspace():
            return ""
        if len(v) > BEFORE_AFTER_LIMIT:
            raise ValidationError("before_after_too_long")

        v = v.rstrip()

        return v

    @validator("slicer")
    def check_slicer(cls, v: str) -> str:
        if v not in [",", ".", ";"]:
            raise ValidationError("slicer_error")
        return v

    @validator("content")
    def check_content(cls, v: str, values) -> str:
        """
        NOTE: Backward compatability
        Allow " " as a value if 'before' or 'after' are not blank.
        Some users use it like this.
        """
        before = values.get("before")
        after = values.get("after")
        before = before.strip()
        after = after.strip()

        if (v == "" or v.isspace()) and after == "" and before == "":
            raise ValidationError("content_blank")
        if len(v.encode("utf-8")) > CONTENT_LIMIT_BYTES:
            raise ValidationError("content_too_long")
        if v.isspace():
            return " "

        v = v.strip()

        return v

    @validator("end")
    def check_end(cls, v: int) -> int:
        try:
            v = int(v)
        except ValueError:
            raise ValidationError("end_error")
        if v >= 1 and v <= 8:
            return v
        else:
            raise ValidationError("end_error")


class BodyValidation(BaseModel):
    blocks: List[BlockValidation]

    sequences: List[str] = []
    exceptions: List[str] = []

    @validator("sequences", "exceptions")
    def check_mods(cls, v: List[str], values):
        """
        It validates and transforms str[] to int[][]

        Input: ["1,2,3,4", "4,3,2, 1 ", " "].
        Output: [[1,2,3,4], [4,3,2,1]]
        """
        pattern = re.compile(r"^\d+(,\d+)*$")
        sequences = [s.strip().replace(" ", "") for s in v if s.strip() != ""]

        try:
            blocks_count = len(values.get("blocks"))
        except TypeError:
            # NOTE: should never be raised
            raise ValidationError("mods_fix_blocks")

        mods = []
        for i, sequence in enumerate(sequences, 1):
            if not re.match(pattern, sequence):
                raise ModValidationError("mods_error_1", i=i)

            mod = [int(n) for n in sequence.split(",")]

            for n in mod:
                if n > blocks_count or n <= 0:
                    raise ModValidationError(
                        "mods_error_2",
                        i=i,
                        blocks_count=blocks_count,
                        n=n,
                    )
            mods.append(mod)

        return mods


class FormatValidation(BaseModel):
    align: str

    @validator("align")
    def check_align(cls, v: str) -> str:
        if v not in ["center", "left", "right", "justify"]:
            raise ValidationError("align_error")
        return v
