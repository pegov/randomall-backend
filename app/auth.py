import asyncio

from aioredis import Redis
from asyncpg import Pool
from fastapi import FastAPI, Request
from fastapi_auth import FastAPIAuthApp, User
from fastapi_auth.backend.authorization.default import DefaultAuthorization
from fastapi_auth.backend.captcha.recaptcha import RecaptchaClient
from fastapi_auth.backend.email.aiosmtplib import AIOSMTPLibEmailClient
from fastapi_auth.backend.oauth import (
    FacebookOAuthProvider,
    GoogleOAuthProvider,
    VKOAuthProvider,
)
from fastapi_auth.backend.password.passlib import PasslibPasswordBackend
from fastapi_auth.backend.transport.cookie import CookieTransport
from fastapi_auth.backend.validator.default import DefaultUserValidator
from fastapi_auth.backend.validator.en_ru import EnRuUserValidator
from fastapi_auth.jwt import TokenParams
from fastapi_auth.models.user import UserUpdate

from app.config import (
    ACCESS_COOKIE_EXPIRATION,
    ACCESS_COOKIE_NAME,
    DEBUG,
    DISPLAY_NAME,
    DOMAIN,
    FACEBOOK_CLIENT_ID,
    FACEBOOK_CLIENT_SECRET,
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
    LANGUAGE,
    ORIGIN,
    PRIVATE_KEY_KID_2,
    PRIVATE_KEY_KID_9,
    PUBLIC_KEY_KID_2,
    PUBLIC_KEY_KID_9,
    RECAPTCHA_SECRET,
    REFRESH_COOKIE_EXPIRATION,
    REFRESH_COOKIE_NAME,
    SMTP_HOST,
    SMTP_PASSWORD,
    SMTP_TLS,
    SMTP_USERNAME,
    SOCIAL_PROVIDERS,
    VK_APP_ID,
    VK_APP_SECRET,
)
from app.db.postgres import PostgresDB
from app.db.redis import RedisCache
from app.entities.events import Event
from app.logger import Logger
from app.repo.events import EventsRepo
from app.repo.gens import GensRepo
from app.repo.lists import ListsRepo
from app.routers.dependencies import get_fastapi_auth_repo
from app.utils.jwt_multi import Algorithm, JWTMultiBackend


async def update_username_hook(
    request: Request, user: User, update_obj: UserUpdate
) -> None:
    if update_obj.username is None:
        return

    db_pool: Pool = request.app.state.db_pool
    cache_pool: Redis = request.app.state.cache_pool

    async with (
        db_pool.acquire() as db_conn,
        cache_pool.client() as cache_conn,
    ):
        db_client = PostgresDB(db_conn)
        cache_client = RedisCache(cache_conn)

        gen_ids = await db_client._conn.fetchval(
            "SELECT COALESCE(array_agg(id), ARRAY[]::integer[]) FROM gen WHERE user_id = $1;",
            user.id,
        )
        list_ids = await db_client._conn.fetchval(
            "SELECT COALESCE(array_agg(id), ARRAY[]::integer[]) FROM list WHERE user_id = $1;",
            user.id,
        )
        assert gen_ids is not None
        assert list_ids is not None

        gens_repo = GensRepo(db_client, cache_client)
        lists_repo = ListsRepo(db_client, cache_client)
        logger = Logger()
        events_repo = EventsRepo(db_client, cache_client, logger)
        await events_repo.create(
            Event.USERS_CHANGE_USERNAME,
            {"old": user.username, "new": update_obj.username},
            user,
        )

        tasks = []
        for gen_id in gen_ids:
            tasks.append(asyncio.create_task(gens_repo.reset_cache(gen_id)))
        for list_id in list_ids:
            tasks.append(asyncio.create_task(lists_repo.reset_cache(list_id)))

        tasks.append(asyncio.create_task(gens_repo.reset_preview()))

        await asyncio.gather(*tasks)


def get_auth_app(app: FastAPI) -> FastAPIAuthApp:
    alg_ed_1 = Algorithm(
        kid="1",
        algorithm="EdDSA",
        private_key=PRIVATE_KEY_KID_1,
        public_key=PUBLIC_KEY_KID_1,
        main=False,
    )
    alg_ed_2_main = Algorithm(
        kid="2",
        algorithm="EdDSA",
        private_key=PRIVATE_KEY_KID_2,
        public_key=PUBLIC_KEY_KID_2,
        main=True,
    )
    alg_fallback = Algorithm(
        kid="9",
        algorithm="RS256",
        private_key=PRIVATE_KEY_KID_9,
        public_key=PUBLIC_KEY_KID_9,
        main=False,
    )
    algs = (
        alg_ed_1,
        alg_ed_2_main,
        alg_fallback,
    )
    jwt_backend = JWTMultiBackend(algs, fallback_kid=alg_fallback.kid)
    token_params = TokenParams(
        access_token_expiration=ACCESS_COOKIE_EXPIRATION,
        refresh_token_expiration=REFRESH_COOKIE_EXPIRATION,
    )

    transport = CookieTransport(
        access_cookie_name=ACCESS_COOKIE_NAME,
        refresh_cookie_name=REFRESH_COOKIE_NAME,
        secure=not DEBUG,
    )
    authorization = DefaultAuthorization()

    password_backend = PasslibPasswordBackend(["bcrypt", "django_pbkdf2_sha256"])

    if LANGUAGE == "RU":
        verification_subject = "Подтверждение email"
        verifiation_message = f"""Добро пожаловать на <a href="{ORIGIN}">{DISPLAY_NAME}</a>!<br /><br />Чтобы подтвердить, что указанный адрес принадлежит вам, <a href="{ORIGIN}/confirm?token={{}}">щелкните здесь</a>.<br /><br />С уважением,<br />администрация сайта {DISPLAY_NAME}"""

        forgot_password_subject = "Забыли пароль"
        forgot_password_message = f"""Кто-то запросил сброс пароля на вашем аккаунте в <a href="{ORIGIN}">{DISPLAY_NAME}</a><br /><br />
            Если это были вы, <a href="{ORIGIN}/reset_password?token={{}}">щелкните здесь</a> для начала процедуры сброса пароля.<br /><br /><br />Если это были не вы, можете проигнорировать это письмо.<br /><br />С уважением,<br />администрация сайта {DISPLAY_NAME}"""

        check_old_email_subject = "Смена email"
        check_old_email_message = f"""Кто-то запросил смену email на вашем аккаунте. Если это были вы, то <a href="{ORIGIN}/check_email?type=old&token={{}}">пройдите по ссылке</a>, чтобы продолжить процедуру.<br /><br />С уважением,<br />администрация сайта {DISPLAY_NAME}"""

        check_new_email_subject = "Смена email"
        check_new_email_message = f"""Подтвердите новый email. Для этого <a href="{ORIGIN}/check_email?type=new&token={{}}">пройдите по ссылке</a>.<br /><br />С уважением,<br />администрация сайта {DISPLAY_NAME}"""

        oauth_account_removal_subject = "Удаление привязки к социальному аккаунту"
        oauth_account_removal_message = f"""Кто-то запросил удаление привязки к социальному аккаунту на вашем аккаунте в <a href="{ORIGIN}">{DISPLAY_NAME}</a>. Если это были вы, то <a href="{ORIGIN}/check_old_email?token{{}}">пройдите по ссылке</a>, чтобы завершить процедуру."""

    else:
        verification_subject = "Confirm email"
        verifiation_message = f"""Welcome to <a href="{ORIGIN}">{DISPLAY_NAME}</a>!<br /><br /><a href="{ORIGIN}/confirm?token={{}}">Click here</a> to complete your sing up<br /><br />Thanks,<br />{DOMAIN} team"""

        forgot_password_subject = "Forgot password"
        forgot_password_message = f"""Password reset has been requested for <a href="{ORIGIN}">{DISPLAY_NAME}</a><br /><br />
            If it was you who did it, <a href="{ORIGIN}/reset_password?token={{}}">click here</a><br /><br /><br /><br />If it was not you, ignore this letter.<br /><br />Thanks,<br />{DOMAIN} team"""

        check_old_email_subject = "Смена email"
        check_old_email_message = f"""Кто-то запросил смену email на вашем аккаунте. Если это были вы, то <a href="{ORIGIN}/email_check_old?token{{}}">пройдите по ссылке</a>, чтобы продолжить процедуру."""

        check_new_email_subject = "Смена email"
        check_new_email_message = f"""Подтвердите новый email. Для этого <a href="{ORIGIN}/email_check_new?token={{}}">пройдите по ссылке</a>."""

        oauth_account_removal_subject = "Удаление привязки к социальному аккаунту"
        oauth_account_removal_message = f"""Кто-то запросил удаление привязки к социальному аккаунту на вашем аккаунте в <a href="{ORIGIN}">{DISPLAY_NAME}</a>. Если это были вы, то <a href="{ORIGIN}/oauth_remove?token{{}}">пройдите по ссылке</a>, чтобы завершить процедуру."""

    email_client = AIOSMTPLibEmailClient(
        hostname=SMTP_HOST,
        username=SMTP_USERNAME,
        password=SMTP_PASSWORD,
        port=SMTP_TLS,
        display_name=DISPLAY_NAME,
        verification_subject=verification_subject,
        verification_message=verifiation_message,
        forgot_password_subject=forgot_password_subject,
        forgot_password_message=forgot_password_message,
        check_old_email_subject=check_old_email_subject,
        check_old_email_message=check_old_email_message,
        check_new_email_subject=check_new_email_subject,
        check_new_email_message=check_new_email_message,
        oauth_account_removal_subject=oauth_account_removal_subject,
        oauth_account_removal_message=oauth_account_removal_message,
    )

    captcha_client = RecaptchaClient(str(RECAPTCHA_SECRET))

    active_providers = []
    for provider in SOCIAL_PROVIDERS:
        if provider == "google":  # pragma: no cover
            google = GoogleOAuthProvider(
                id=GOOGLE_CLIENT_ID,
                secret=GOOGLE_CLIENT_SECRET,
            )
            active_providers.append(google)
            continue
        if provider == "vk":  # pragma: no cover
            vk = VKOAuthProvider(
                id=VK_APP_ID,
                secret=VK_APP_SECRET,
                login_only=True,
            )
            active_providers.append(vk)
            continue
        if provider == "facebook":  # pragma: no cover
            facebook = FacebookOAuthProvider(
                id=FACEBOOK_CLIENT_ID,
                secret=FACEBOOK_CLIENT_SECRET,
                login_only=True,
            )
            active_providers.append(facebook)

    forbidden_usernames = [
        "edit",
        "dev",
        "notifications",
        "settings",
        "me",
        "main",
        "info",
        "description",
        "links",
        "private",
        "develop",
        "developer",
        "gens",
        "lists",
        "engines",
        "vh",
    ]
    if LANGUAGE == "EN":
        validator = DefaultUserValidator(forbidden_usernames=forbidden_usernames)
    else:
        validator = EnRuUserValidator(forbidden_usernames=forbidden_usernames)

    auth_app = FastAPIAuthApp(
        app,
        get_fastapi_auth_repo,
        jwt_backend,
        token_params,
        transport,
        authorization,
        active_providers,
        password_backend,
        email_client,
        captcha_client,
        validator,
        on_update_action=update_username_hook,
        origin=ORIGIN,
        debug=DEBUG,
    )
    return auth_app
