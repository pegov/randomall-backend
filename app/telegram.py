from aiogram import Bot

from app.config import TELEGRAM_CHAT_ID, TELEGRAM_TOKEN
from app.meta import Singleton
from app.utils import warning


class TelegramNotifier(metaclass=Singleton):
    def __init__(self, domain: str, origin: str, language: str) -> None:
        if TELEGRAM_TOKEN is None or TELEGRAM_TOKEN == "":
            raise RuntimeError("TELEGRAM TOKEN is None!")

        self._bot = Bot(TELEGRAM_TOKEN, parse_mode="MarkdownV2")
        self._domain = domain
        self._origin = origin

        if language == "RU":
            self._profile_path = "profile"
            self._gens_path = "custom/gen"
        else:
            self._profile_path = "profiles"
            self._gens_path = "gens"

        self._stopwords = warning.get_stopwords(language)

    @staticmethod
    def _escape_msg(msg: str) -> str:
        for ch in [
            "_",
            "*",
            "[",
            "]",
            "(",
            ")",
            "~",
            "`",
            ">",
            "#",
            "+",
            "-",
            "=",
            "|",
            "{",
            "}",
            ".",
            "!",
        ]:
            msg = msg.replace(ch, f"\\{ch}")
        return msg

    async def _send_notification(self, msg: str) -> None:  # pragma: no cover
        escaped_domain = self._escape_msg(self._domain)
        msg = f"{escaped_domain}\n{msg}"
        await self._bot.send_message(
            TELEGRAM_CHAT_ID,
            msg,
            disable_web_page_preview=True,
        )

    async def notify_on_captcha(self) -> None:
        await self._send_notification("*ТЕМП КАПТЧА АКТИВИРОВАНА*")

    async def notify_on_ban(self) -> None:
        await self._send_notification("*ТЕМП БАН АКТИВИРОВАН*")
