import json
from typing import List, Tuple, Type

from app.db.postgres import PostgresDB
from app.db.redis import RedisCache
from app.entities.settings import (
    GeneralSetting,
    GensSetting,
    ListsSetting,
    Setting,
    SettingsCol,
)
from app.models.settings import Action, ChangeSetting, Kind


class SettingsRepo:
    temp_prefix: str = "settings:temp"

    def __init__(self, db: PostgresDB, cache: RedisCache) -> None:
        self._db = db
        self._cache = cache

    async def on_startup(self) -> None:
        cols: List[Type[SettingsCol]] = [GensSetting, ListsSetting, GeneralSetting]
        for col in cols:
            for setting in col.perm():
                value = await self._db.settings.get_setting(setting)
                col.set_value(setting, value)
            for setting in col.temp():
                t_value, _ = await self.get_temp(setting)
                if t_value:
                    col.set_temp(setting, True)

    def _temp_key(self, setting: Setting) -> str:
        return f"{self.temp_prefix}:{setting.section}:{setting.name}"

    async def get_temp(self, setting: Setting) -> Tuple[bool, int]:
        key = self._temp_key(setting)
        value = await self._cache.get(key)
        if value is None:
            return False, 0

        ttl = await self._cache.ttl(key)
        return True, ttl

    async def set_temp(
        self, setting: Setting, value: int | str | bool, ex: int
    ) -> None:
        key = self._temp_key(setting)
        if isinstance(value, bool):
            value = 1
        await self._cache.set(key, value, ex)

    async def delete_temp(self, setting: Setting) -> None:
        key = self._temp_key(setting)
        await self._cache.delete(key)

    def _get_col(self, setting: Setting) -> Type[SettingsCol]:
        match setting.section:
            case "gens":
                return GensSetting
            case "lists":
                return ListsSetting
            case "general":
                return GeneralSetting
            case _:
                raise Exception("Wrong setting section", setting.section)

    async def get(self, setting: Setting) -> int | str | bool:
        col = self._get_col(setting)
        s = getattr(col, setting.name)
        if s.temp:
            t_value, ttl = await self.get_temp(setting)
            if t_value:
                return t_value
            else:
                col.set_temp(setting, False)

        return setting.value

    async def get_perm_int(self, setting: Setting) -> int:
        return await self.get(setting)  # type: ignore

    async def get_perm_str(self, setting: Setting) -> str:
        return await self.get(setting)  # type: ignore

    async def get_perm_bool(self, setting: Setting) -> bool:
        return await self.get(setting)  # type: ignore

    async def set(self, setting: Setting, value: int | str | bool) -> None:
        await self._db.settings.set_setting(setting, value)
        col = self._get_col(setting)
        col.set_value(setting, value)

    async def perm_to_dict(self, settings: Type[SettingsCol]) -> dict:
        d = {}
        for setting in settings.perm():
            d[setting.name] = await self.get(setting)

        return d

    async def temp_to_dict(self, settings: Type[SettingsCol]) -> dict:
        d = {}
        temp = settings.temp()
        for member in temp:
            value, ttl = await self.get_temp(member)
            d[member.name] = {
                "value": value,
                "ttl": ttl,
            }

        return d

    async def change_setting(
        self,
        setting: Setting,
        data: ChangeSetting,
    ) -> bool:
        if data.kind is Kind.PERM and data.action is Action.SET:
            if data.value_type() is not setting.type():
                return False

            await self.set(setting, data.value())
            return True

        elif (
            data.kind is Kind.TEMP and data.action is Action.SET and data.ex is not None
        ):
            if data.value_type() is not setting.type():
                return False

            await self.set_temp(setting, data.value(), data.ex)
            return True

        elif data.kind is Kind.TEMP and data.action is Action.DELETE:
            await self.delete_temp(setting)
            return True

        return False

    async def pub(self, ch: str, msg: dict) -> None:
        conn = self._cache.conn
        subs = dict(await conn.pubsub_numsub(ch))
        if subs[ch] > 0:
            await conn.publish(ch, json.dumps(msg))
