import logging
import logging.handlers
from datetime import datetime, timezone

from fastapi_auth import User

from app.config import DEBUG, LANGUAGE
from app.entities.events import Ev, Event
from app.meta import Singleton
from app.utils.json import obj_to_json_str

ROOT = "/var/log/randomall"


def create_editor_log(ev: Ev, user: User, ip: str, item_id: int):
    return {
        "event": ev.sname,
        "ip": "0.0.0.0",
        "id": item_id,
        "user": {
            "id": user.id,
            "username": user.username,
        },
    }


class LevelFilter:
    def __init__(self, level):
        self._level = level

    def filter(self, log_record):
        return log_record.levelno == self._level


def create_logger(name: str, level: int, filepath: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(level)
    if DEBUG:
        handler = logging.StreamHandler()  # type: ignore
    else:
        handler = logging.FileHandler(f"{ROOT}{filepath}")  # type: ignore

    formatter = logging.Formatter("%(asctime)s %(message)s")
    formatter.formatTime = (  # type: ignore
        lambda record, datefmt=None: datetime.fromtimestamp(
            record.created, timezone.utc
        )
        .astimezone()
        .isoformat(sep="T", timespec="milliseconds")
    )

    handler.setFormatter(formatter)

    logger.addFilter(LevelFilter(level=level))  # type: ignore
    logger.addHandler(handler)

    return logger


class EditorErrorMixin:
    editor_error: logging.Logger

    def error(self, ev: Ev, e: Exception) -> None:
        self.editor_error.error(f"[{ev.sname}] {e}", exc_info=True, stack_info=True)


class GensLoggers(EditorErrorMixin):
    def __init__(self) -> None:
        self.editor_backup = create_logger(
            "gens-editor-backup",
            logging.INFO,
            "/gens/editor-backup.log",
        )
        self.editor_error = create_logger(
            "gens-editor-error",
            logging.ERROR,
            "/gens/editor-error.log",
        )
        self.editor_event = create_logger(
            "gens-editor",
            logging.INFO,
            "/gens/editor-event.log",
        )

        self.result = create_logger(
            "gens-result",
            logging.INFO,
            "/gens/result.log",
        )
        self.result_ratelimit = create_logger(
            "gens-ratelimit",
            logging.INFO,
            "/gens/ratelimit.log",
        )
        self.search = create_logger(
            "gens-search",
            logging.INFO,
            "/gens/search.log",
        )

    def event(self, ev: Ev, data: dict):
        log_str = obj_to_json_str(data)
        match ev.name:
            case Event.GENS_EDITOR_CREATE.name | Event.GENS_EDITOR_EDIT.name | Event.GENS_EDITOR_DELETE.name:
                self.editor_event.info(log_str)
            case Event.GENS_EDITOR_BACKUP.name:
                self.editor_backup.info(log_str)
            case Event.GENS_RESULT.name:
                self.result.info(log_str)
            case Event.GENS_RESULT_RATELIMIT.name:
                self.result_ratelimit.info(log_str)
            case Event.GENS_SEARCH.name:
                self.search.info(log_str)
            case _:
                raise Exception("Wrong event:", ev)


class ListsLoggers(EditorErrorMixin):
    def __init__(self) -> None:
        self.editor_error = create_logger(
            "lists-editor-error",
            logging.ERROR,
            "/lists/editor-error.log",
        )
        self.editor_event = create_logger(
            "lists-editor-events",
            logging.INFO,
            "/lists/editor-event.log",
        )

    def event(self, ev: Ev, data: dict):
        log_str = obj_to_json_str(data)
        match ev.name:
            case Event.LISTS_EDITOR_CREATE.name | Event.LISTS_EDITOR_EDIT.name | Event.LISTS_EDITOR_DELETE.name:
                self.editor_event.info(log_str)
            case _:
                raise Exception("Wrong event:", ev)


class GeneralLoggers:
    def __init__(self) -> None:
        self.result = create_logger(
            "general-result",
            logging.INFO,
            "/general/result.log",
        )
        self.ratelimit = create_logger(
            "general-ratelimit",
            logging.INFO,
            "/general/ratelimit.log",
        )

    def event(self, ev: Ev, data: dict):
        log_str = obj_to_json_str(data)
        match ev.name:
            case Event.GENERAL_RESULT.name:
                self.result.info(log_str)
            case Event.GENERAL_RESULT_RATELIMIT.name:
                self.ratelimit.info(log_str)


class UsersLogger:
    def __init__(self) -> None:
        self.change_username = create_logger(
            "users-change-username",
            logging.INFO,
            "/users/change_username.log",
        )

    def event(self, ev: Ev, data: dict):
        log_str = obj_to_json_str(data)
        match ev.name:
            case Event.USERS_CHANGE_USERNAME.name:
                self.change_username.info(log_str)


class ProfilesLogger:
    def __init__(self) -> None:
        self.info = create_logger(
            "info",
            logging.INFO,
            "/profiles/info.log",
        )

    def event(self, ev: Ev, data: dict):
        log_str = obj_to_json_str(data)
        match ev.name:
            case Event.PROFILES_INFO_EDIT.name:
                self.info.info(log_str)


class Logger(metaclass=Singleton):
    fastapi_auth: logging.Logger
    gens: GensLoggers
    lists: ListsLoggers
    general: GeneralLoggers

    def create_fastapi_auth_logger(self) -> None:
        self.fastapi_auth = create_logger(
            "fastapi-auth",
            logging.INFO,
            "/users/fastapi-auth.log",
        )

    def __init__(self) -> None:
        self.gens = GensLoggers()
        self.lists = ListsLoggers()
        self.users = UsersLogger()
        self.profiles = ProfilesLogger()
        if LANGUAGE == "RU":
            self.general = GeneralLoggers()
        self.fastapi_auth = create_logger(
            "fastapi-auth",
            logging.INFO,
            "/users/fastapi-auth.log",
        )

    def event(self, ev: Ev, data: dict) -> None:
        match ev.category:
            case "gens":
                self.gens.event(ev, data)
            case "lists":
                self.lists.event(ev, data)
            case "general":
                self.general.event(ev, data)
            case "profiles":
                self.profiles.event(ev, data)
            case "users":
                self.users.event(ev, data)
            case _:
                raise Exception("Wrong event category:", ev.category)
