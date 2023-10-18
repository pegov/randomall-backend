from typing import Optional

from httpx import AsyncClient

from app.config import RECAPTCHA_SECRET


async def is_captcha_valid(captcha: Optional[str]) -> bool:
    if captcha is None:
        return False

    async with AsyncClient(
        base_url="https://www.google.com"
    ) as client:  # pragma: nocover
        response = await client.post(
            "/recaptcha/api/siteverify",
            data={
                "secret": RECAPTCHA_SECRET,
                "response": captcha,
            },
        )
        return response.json().get("success")
