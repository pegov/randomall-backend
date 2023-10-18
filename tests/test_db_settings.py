import pytest

from asyncpg import Connection

from app.db.postgres.settings import SettingsExt
from app.entities.settings import GensSetting

pytestmark = pytest.mark.anyio


@pytest.fixture
def settings_ext(db_conn: Connection):
    return SettingsExt(db_conn)


async def test_get_setting(settings_ext: SettingsExt):
    setting = GensSetting.EDITOR_PING_INTERVAL
    res = await settings_ext.get_setting(setting)
    assert res == setting.value


async def test_set_setting(settings_ext: SettingsExt):
    setting = GensSetting.EDITOR_PING_INTERVAL
    value = 10
    await settings_ext.set_setting(setting, value)
    res = await settings_ext.get_setting(setting)
    assert res == value
