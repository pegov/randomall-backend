import pytest

from asyncpg import Connection

from app.db.postgres.profiles import ProfilesExt

pytestmark = pytest.mark.anyio


@pytest.fixture
def profiles_ext(db_conn: Connection):
    return ProfilesExt(db_conn)


async def test_create_notification(profiles_ext: ProfilesExt):
    await profiles_ext.create_notification(1, "test message")


async def test_get_notifications(profiles_ext: ProfilesExt):
    USER_ID = 1
    MESSAGE = "test message"
    await profiles_ext.create_notification(USER_ID, MESSAGE)

    items = await profiles_ext.get_notifications(USER_ID)
    item = items[0]
    assert item.get("user_id") == USER_ID
    assert item.get("message") == MESSAGE
    assert item.get("seen") is False


async def test_see_notifications(profiles_ext: ProfilesExt):
    USER_ID = 1
    MESSAGE = "test message"
    await profiles_ext.create_notification(USER_ID, MESSAGE)

    items = await profiles_ext.get_notifications(USER_ID)
    item = items[0]
    assert item.get("user_id") == USER_ID
    assert item.get("message") == MESSAGE
    assert item.get("seen") is False

    await profiles_ext.see_notifications(USER_ID)

    items = await profiles_ext.get_notifications(USER_ID)
    item = items[0]
    assert item.get("seen") is True


# TODO:
async def test_get_gens_for_owner(profiles_ext: ProfilesExt):
    items = await profiles_ext.get_gens_for_owner(1)
    assert isinstance(items, list)


async def test_get_gens_for_guest(profiles_ext: ProfilesExt):
    items = await profiles_ext.get_gens_for_guest(1)
    assert isinstance(items, list)


async def test_get_lists_for_owner(profiles_ext: ProfilesExt):
    items = await profiles_ext.get_lists_for_owner(1)
    assert isinstance(items, list)


async def test_get_lists_for_guest(profiles_ext: ProfilesExt):
    items = await profiles_ext.get_lists_for_guest(1)
    assert isinstance(items, list)


async def test_get_gens_fav(profiles_ext: ProfilesExt):
    items = await profiles_ext.get_gens_fav(1)
    assert isinstance(items, list)
