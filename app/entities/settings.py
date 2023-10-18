from typing import Iterable, NamedTuple


class Setting(NamedTuple):
    section: str
    name: str
    value: int | str | bool
    temp: bool

    def type(self):
        return type(self.value)


class SettingsCol:
    @classmethod
    def section(cls) -> str:
        raise NotImplementedError

    @classmethod
    def temp(cls) -> Iterable[Setting]:
        return tuple()

    @classmethod
    def perm(cls) -> Iterable[Setting]:
        raise NotImplementedError

    @classmethod
    def set_value(cls, setting: Setting, value: int | str | bool) -> None:
        setattr(
            cls,
            setting.name,
            Setting(
                section=setting.section,
                name=setting.name,
                value=value,
                temp=setting.temp,
            ),
        )

    @classmethod
    def set_temp(cls, setting: Setting, temp: bool) -> None:
        setattr(
            cls,
            setting.name,
            Setting(
                section=setting.section,
                name=setting.name,
                value=setting.value,
                temp=temp,
            ),
        )


class GensSetting(SettingsCol):
    EDITOR_PING_INTERVAL = Setting("gens", "EDITOR_PING_INTERVAL", 60, False)

    EDITOR_SAVE_BAN_CREATE = Setting("gens", "EDITOR_SAVE_BAN_CREATE", False, False)
    EDITOR_SAVE_BAN_EDIT = Setting("gens", "EDITOR_SAVE_BAN_EDIT", False, False)
    EDITOR_CAPTCHA_CREATE = Setting("gens", "EDITOR_CAPTCHA_CREATE", False, False)
    EDITOR_CAPTCHA_EDIT = Setting("gens", "EDITOR_CAPTCHA_EDIT", False, False)

    EDITOR_SPAM_CAPTCHA_LIMIT = Setting("gens", "EDITOR_SPAM_CAPTCHA_LIMIT", 25, False)
    EDITOR_SPAM_BAN_LIMIT = Setting("gens", "EDITOR_SPAM_BAN_LIMIT", 50, False)
    EDITOR_SPAM_CAPTCHA_DURATION = Setting(
        "gens", "EDITOR_SPAM_CAPTCHA_DURATION", 3600, False
    )
    EDITOR_SPAM_BAN_DURATION = Setting("gens", "EDITOR_SPAM_BAN_DURATION", 3600, False)

    VIEW_SUGGESTIONS_COUNT = Setting("gens", "VIEW_SUGGESTIONS_COUNT", 8, False)
    VIEW_SUGGESTIONS_LIKES_THRESHOLD = Setting(
        "gens",
        "VIEW_SUGGESTIONS_LIKES_THRESHOLD",
        0,
        False,
    )
    VIEW_RESULT_RATELIMIT = Setting("gens", "VIEW_RESULT_RATELIMIT", 8, False)
    VIEW_PREVIEW_COUNT = Setting("gens", "VIEW_PREVIEW_COUNT", 6, False)

    SEARCH_PAGE_SIZE = Setting("gens", "SEARCH_PAGE_SIZE", 15, False)

    @classmethod
    def section(cls) -> str:
        return "gens"

    @classmethod
    def perm(cls) -> Iterable[Setting]:
        return (
            cls.EDITOR_PING_INTERVAL,
            cls.EDITOR_SAVE_BAN_CREATE,
            cls.EDITOR_SAVE_BAN_EDIT,
            cls.EDITOR_CAPTCHA_CREATE,
            cls.EDITOR_CAPTCHA_EDIT,
            cls.EDITOR_SPAM_CAPTCHA_LIMIT,
            cls.EDITOR_SPAM_BAN_LIMIT,
            cls.EDITOR_SPAM_CAPTCHA_DURATION,
            cls.EDITOR_SPAM_BAN_DURATION,
            cls.VIEW_SUGGESTIONS_COUNT,
            cls.VIEW_SUGGESTIONS_LIKES_THRESHOLD,
            cls.VIEW_RESULT_RATELIMIT,
            cls.VIEW_PREVIEW_COUNT,
            cls.SEARCH_PAGE_SIZE,
        )

    @classmethod
    def temp(cls) -> Iterable[Setting]:
        return (
            cls.EDITOR_SAVE_BAN_CREATE,
            cls.EDITOR_SAVE_BAN_EDIT,
            cls.EDITOR_CAPTCHA_CREATE,
            cls.EDITOR_CAPTCHA_EDIT,
        )  # type: ignore


class ListsSetting(SettingsCol):
    EDITOR_SAVE_BAN_CREATE = Setting("lists", "EDITOR_SAVE_BAN_CREATE", False, False)
    EDITOR_SAVE_BAN_EDIT = Setting("lists", "EDITOR_SAVE_BAN_EDIT", False, False)
    EDITOR_CAPTCHA_CREATE = Setting("lists", "EDITOR_CAPTCHA_CREATE", False, False)
    EDITOR_CAPTCHA_EDIT = Setting("lists", "EDITOR_CAPTCHA_EDIT", False, False)

    EDITOR_SPAM_CAPTCHA_LIMIT = Setting("lists", "EDITOR_SPAM_CAPTCHA_LIMIT", 25, False)
    EDITOR_SPAM_BAN_LIMIT = Setting("lists", "EDITOR_SPAM_BAN_LIMIT", 50, False)

    SEARCH_PAGE_SIZE = Setting("lists", "SEARCH_PAGE_SIZE", 30, False)

    @classmethod
    def section(cls) -> str:
        return "lists"

    @classmethod
    def perm(cls) -> Iterable[Setting]:
        return (
            cls.EDITOR_SAVE_BAN_CREATE,
            cls.EDITOR_SAVE_BAN_EDIT,
            cls.EDITOR_CAPTCHA_CREATE,
            cls.EDITOR_CAPTCHA_EDIT,
            cls.SEARCH_PAGE_SIZE,
        )

    @classmethod
    def temp(cls) -> Iterable[Setting]:
        return (
            cls.EDITOR_SAVE_BAN_CREATE,
            cls.EDITOR_SAVE_BAN_EDIT,
            cls.EDITOR_CAPTCHA_CREATE,
            cls.EDITOR_CAPTCHA_EDIT,
            cls.EDITOR_SPAM_CAPTCHA_LIMIT,
            cls.EDITOR_SPAM_BAN_LIMIT,
        )  # type: ignore


class GeneralSetting(SettingsCol):
    RESULT_RATELIMIT = Setting("general", "RESULT_RATELIMIT", 8, False)
    INFO_EXPIRE = Setting("general", "INFO_EXPIRE", 3600, False)
    DRM = ""

    @classmethod
    def section(cls) -> str:
        return "general"

    @classmethod
    def perm(cls) -> Iterable[Setting]:
        return (
            cls.RESULT_RATELIMIT,
            cls.INFO_EXPIRE,
        )
