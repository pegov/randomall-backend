from typing import Iterable

from starlette.config import Config
from starlette.datastructures import CommaSeparatedStrings, Secret

VERSION = "0.0.1"

config = Config()

# Base
DEBUG: bool = config("DEBUG", cast=bool, default=True)
ORIGIN: str = config("ORIGIN", default="http://127.0.0.1")
DOMAIN: str = config("DOMAIN", default="127.0.0.1")
DISPLAY_NAME: str = config("DISPLAY_NAME", default="127.0.0.1")
LANGUAGE: str = config("LANGUAGE", default="RU")

# Database
DATABASE_USERNAME: str = config("DATABASE_USERNAME", default="postgres")
DATABASE_PASSWORD: str = config("DATABASE_PASSWORD", default="postgres")
DATABASE_HOST: str = config("DATABASE_HOST", default="localhost")
DATABASE_PORT: str = config("DATABASE_PORT", default="5432")
DATABASE_NAME: str = config("DATABASE_NAME", default="randomall")

# Cache
CACHE_URL: str = config("CACHE_URL", default="redis://localhost:6379/")

# Auth
JWT_ALGORITHM = "EdDSA"
with open("./ed25519_2.key", "r") as f:
    PRIVATE_KEY_KID_2 = f.read()

with open("./ed25519_2.pub", "r") as f:
    PUBLIC_KEY_KID_2 = f.read()

with open("./rsa.key", "r") as f:
    PRIVATE_KEY_KID_9 = f.read()

with open("./rsa.pub", "r") as f:
    PUBLIC_KEY_KID_9 = f.read()

ACCESS_COOKIE_EXPIRATION: int = 60 * 60 * 6
REFRESH_COOKIE_EXPIRATION: int = 60 * 60 * 24 * 31

ACCESS_COOKIE_NAME: str = config("ACCESS_COOKIE_NAME", default="access")
REFRESH_COOKIE_NAME: str = config("REFRESH_COOKIE_NAME", default="refresh")

SECRET_KEY: Secret = config("SECRET_KEY", cast=Secret, default=Secret("secret"))

# Email client
SMTP_USERNAME: str = config("SMTP_USERNAME", default="")
SMTP_PASSWORD: str = config("SMTP_PASSWORD", default="")
SMTP_HOST: str = config("SMTP_HOST", default="")
SMTP_TLS: int = config("SMTP_TLS", cast=int, default=465)

# Social providers
SOCIAL_PROVIDERS: Iterable = config(
    "SOCIAL_PROVIDERS", cast=CommaSeparatedStrings, default=[]
)
FACEBOOK_CLIENT_ID: str = config("FACEBOOK_CLIENT_ID", default="")
FACEBOOK_CLIENT_SECRET: str = config("FACEBOOK_CLIENT_SECRET", default="")

GOOGLE_CLIENT_ID: str = config("GOOGLE_CLIENT_ID", default="")
GOOGLE_CLIENT_SECRET: str = config("GOOGLE_CLIENT_SECRET", default="")

VK_APP_ID: str = config("VK_APP_ID", default="")
VK_APP_SECRET: str = config("VK_APP_SECRET", default="")

# Captcha
RECAPTCHA_SECRET: Secret = config("RECAPTCHA_SECRET", cast=Secret, default=Secret(""))

# Notifications
TELEGRAM_TOKEN: str = config("TELEGRAM_TOKEN", default="")
TELEGRAM_CHAT_ID: str = config("TELEGRAM_CHAT_ID", default="")


# App settings
API_GENS_PREFIX: str = config("API_GENS_PREFIX", default="/api/gens")
API_LISTS_PREFIX: str = config("API_LISTS_PREFIX", default="/api/lists")
API_USERS_PREFIX: str = config("API_USERS_PREFIX", default="/api/users")

LEGACY_API_CUSTOM_GENS_PREFIX: str = "/api/custom/gens"

GENS_PREFIX: str = config("GENS_PREFIX", default="/gen")

LISTS_PREFIX: str = config("LISTS_PREFIX", default="/list")

PROFILES_PREFIX: str = config("PROFILES_PREFIX", default="/profile")
