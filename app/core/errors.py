from pydantic import ValidationError

from app.core.localization import t


class BaseException(Exception):
    pass


class HeadValidationError(BaseException):
    def __init__(self, e: ValidationError) -> None:
        humanized_errors = []
        self.server_error = False
        for error in e.errors():
            loc = error.get("loc")
            msg = error.get("msg")
            if "Error" in msg:
                msg = t["SERVER_ERROR"]  # type: ignore
                self.server_error = True
            label = t["head"]["labels"].get(loc[0])  # type: ignore
            humanized_errors.append(f"__ERROR__ {label} - {msg}")

        self.error_message = "\n".join(humanized_errors)

    def get_msg(self) -> dict:
        return {
            "msg": self.error_message,
        }


class BodyValidationError(BaseException):
    def __init__(self, e: ValidationError) -> None:
        raise NotImplementedError

    def get_msg(self) -> dict:
        raise NotImplementedError


class FormatValidationError(BaseException):
    def __init__(self, e: ValidationError) -> None:
        raise NotImplementedError

    def get_msg(self) -> dict:
        raise NotImplementedError
