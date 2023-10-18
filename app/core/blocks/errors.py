from pydantic import ValidationError

from app.core.errors import BodyValidationError, FormatValidationError
from app.core.localization import t


class BlocksFormatValidationError(FormatValidationError):
    def __init__(self, e: ValidationError) -> None:
        humanized_errors = []
        self.server_error = False
        for error in e.errors():
            loc = error.get("loc")
            msg = error.get("msg")
            if "Error" in msg:
                msg = t["SERVER_ERROR"]  # type: ignore
                self.server_error = True
            label = t["format"]["labels"].get(loc[0])  # type: ignore
            humanized_errors.append(f"__ERROR__ {label} - {msg}")

        self.error_message = "\n".join(humanized_errors)

    def get_msg(self) -> dict:
        return {
            "msg": self.error_message,
        }


class BlocksEngineValidationError(BodyValidationError):
    def __init__(self, e: ValidationError) -> None:
        humanized_errors = []
        self.blocks_with_errors = []
        self.server_error = False
        for error in e.errors():
            loc = error.get("loc")
            msg = error.get("msg")
            if "Error" in msg:
                msg = t["SERVER_ERROR"]  # type: ignore
                self.server_error = True
            if len(loc) == 3:
                label = t["body"]["blocks"]["labels"].get(loc[2])  # type: ignore
                humanized_errors.append(
                    f"__ERROR__ {t['body']['blocks']['labels'].get('block')} #{loc[1]+1}: {label} - {msg}"  # type: ignore
                )
                self.blocks_with_errors.append(loc[1])
        self.error_message = "\n".join(humanized_errors)
        self.blocks_with_errors = list(set(self.blocks_with_errors))

    def get_msg(self) -> dict:
        return {
            "msg": self.error_message,
            "blocks": self.blocks_with_errors,
        }
