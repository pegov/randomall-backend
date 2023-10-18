from asyncpg import Connection

from app.entities.settings import Setting


class SettingsExt:
    def __init__(self, conn: Connection) -> None:
        self._conn = conn

    async def get_setting(self, setting: Setting) -> int | str | bool:
        t = setting.type()
        if t is int:
            value_field = "i_value"
        elif t is str:
            value_field = "s_value"
        elif t is bool:
            value_field = "b_value"
        else:
            raise Exception(
                f"Wrong value type: {t} in {setting} for name {setting.name}"
            )

        value = await self._conn.fetchval(
            f"SELECT {value_field} FROM global_setting WHERE section = $1 AND name = $2;",
            setting.section,
            setting.name,
        )
        if value is None:
            value = setting.value
            await self.set_setting(setting, value)

        return value

    async def get_int_setting(self, setting: Setting) -> int:
        return await self.get_setting(setting)  # type: ignore

    async def get_str_setting(self, setting: Setting) -> str:
        return await self.get_setting(setting)  # type: ignore

    async def get_bool_setting(self, setting: Setting) -> bool:
        return await self.get_setting(setting)  # type: ignore

    async def set_setting(self, setting: Setting, value: int | str | bool) -> None:
        t = type(value)
        if t is int:
            value_field = "i_value"
        elif t is str:
            value_field = "s_value"
        elif t is bool:
            value_field = "b_value"
        else:
            raise Exception("Wrong value type! Must be int | str | bool")

        async with self._conn.transaction():
            if (
                await self._conn.fetchrow(
                    "SELECT * FROM global_setting WHERE section = $1 AND name= $2;",
                    setting.section,
                    setting.name,
                )
                is None
            ):
                await self._conn.execute(
                    f"INSERT INTO global_setting(section, name, {value_field}) VALUES ($1, $2, $3);",
                    setting.section,
                    setting.name,
                    value,
                )
            else:
                await self._conn.execute(
                    f"UPDATE global_setting SET {value_field} = $3 WHERE section = $1 AND name = $2;",
                    setting.section,
                    setting.name,
                    value,
                )
