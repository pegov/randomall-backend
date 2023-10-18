from pathlib import Path
from random import randint, sample
from typing import List, Optional, Union

from asyncpg import Connection
from sqlsl import Queries

from app.db.postgres.common import dict_or_none

SIMILARITY = 0.5


class GeneralQ(Queries):
    get_info_by_name: str
    get_all_info: str
    get_plot_count: str

    # generate

    get_general_result: str
    get_creative_result: str

    get_superpowers: str

    toggle_usergen: str

    get_creative_by_value: str

    suggest: str

    get_first_unchecked_usergen: str
    get_first_unchecked_wp: str
    get_all_checked_usergen_in_category: str


path = Path(__file__).parent / "sql" / "general.sql"
q = GeneralQ().from_file(path)


class GeneralMeta:
    cities_count: Optional[int] = None
    countries_count: Optional[int] = None
    names_male_count: Optional[int] = None
    names_female_count: Optional[int] = None
    surnames_count: Optional[int] = None

    awkward_moment_count: Optional[int] = None
    unexpected_event_count: Optional[int] = None
    bookname_count: Optional[int] = None
    character_count: Optional[int] = None
    crowd_count: Optional[int] = None
    features_count: Optional[int] = None
    jobs_count: Optional[int] = None
    motivation_count: Optional[int] = None
    plot_count: Optional[int] = None
    race_count: Optional[int] = None
    superpowers_count: Optional[int] = None
    wp_count: Optional[int] = None


def reset_meta(name: str) -> None:
    setattr(GeneralMeta, f"{name}_count", None)


class GeneralExt:
    def __init__(self, conn: Connection) -> None:
        self._conn = conn

    async def get_info(self, name: str) -> Optional[dict]:
        return dict_or_none(await self._conn.fetchrow(q.get_info_by_name, name))

    async def get_all_info(self) -> List[dict]:
        rows = await self._conn.fetch(q.get_all_info)
        return [dict(row) for row in rows]

    async def get_plot_count(self) -> dict:
        return dict(await self._conn.fetchrow(q.get_plot_count))  # type: ignore

    async def _general_basic(self, name: str) -> str:
        attr = f"{name}_count"
        table = f"general_{name}"
        if getattr(GeneralMeta, attr) is None:
            setattr(
                GeneralMeta,
                attr,
                await self._conn.fetchval(f"SELECT COUNT(*) FROM {table}"),
            )
        r_id = randint(1, getattr(GeneralMeta, attr))
        return await self._conn.fetchval(
            q.get_general_result.format(table), r_id
        )  # type: ignore

    async def get_general_result(
        self,
        name: str,
        data: Optional[dict] = None,
    ) -> str:
        if name == "names":
            if data is None or data.get("sex") == 1:  # type: ignore
                name = "names_male"
            else:
                name = "names_female"

        return await self._general_basic(name)

    async def _creative_basic(self, name: str) -> str:
        attr = f"{name}_count"
        table = f"creative_{name}"
        if getattr(GeneralMeta, attr) is None:
            setattr(
                GeneralMeta,
                attr,
                await self._conn.fetchval(f"SELECT COUNT(*) FROM {table}"),
            )
        r_id = randint(0, getattr(GeneralMeta, attr) - 1)
        return await self._conn.fetchval(
            q.get_creative_result.format(table),
            r_id,
        )  # type: ignore

    async def get_creative_result(
        self,
        name: str,
        data: Optional[dict] = None,
        count: int = 1,
    ) -> Union[str, List[str], dict]:  # type: ignore
        if name == "plot":
            if GeneralMeta.plot_count is None:
                GeneralMeta.plot_count = await self._conn.fetchval(
                    "SELECT COUNT(*) FROM creative_plot"
                )  # type: ignore
            if GeneralMeta.wp_count is None:
                GeneralMeta.wp_count = await self._conn.fetchval(
                    "SELECT COUNT(*) FROM creative_wp"
                )  # type: ignore

            r_temp = randint(1, GeneralMeta.plot_count + GeneralMeta.wp_count)  # type: ignore
            if r_temp <= GeneralMeta.plot_count:  # type: ignore
                return await self._creative_basic("plot")
            else:
                return await self._creative_basic("wp")

        elif name == "character":
            table = "creative_character"
            if GeneralMeta.character_count is None:
                GeneralMeta.character_count = await self._conn.fetchval(
                    f"SELECT COUNT(*) FROM {table}"
                )  # type: ignore

            r_sample = sample(range(GeneralMeta.character_count), k=count)  # type: ignore

            res = []
            for v in r_sample:
                res.append(
                    await self._conn.fetchval(q.get_creative_result.format(table), v)
                )
            return res
        elif name == "features":
            table = "creative_features"
            if GeneralMeta.features_count is None:
                GeneralMeta.features_count = await self._conn.fetchval(
                    f"SELECT COUNT(*) FROM {table}"
                )  # type: ignore

            r_sample = sample(range(GeneralMeta.features_count), k=count)  # type: ignore

            res = []
            for v in r_sample:
                res.append(
                    await self._conn.fetchval(q.get_creative_result.format(table), v)
                )
            return res
        elif name == "superpowers":
            table = "creative_superpowers"
            if GeneralMeta.superpowers_count is None:
                GeneralMeta.superpowers_count = await self._conn.fetchval(  # type: ignore
                    f"SELECT COUNT(*) FROM {table}"
                )

            r_id = randint(0, GeneralMeta.superpowers_count - 1)  # type: ignore
            return await self._conn.fetchrow(q.get_superpowers, r_id)  # type: ignore

        return await self._creative_basic(name)

    async def toggle_usergen(self, name: str) -> None:
        await self._conn.execute(q.toggle_usergen, name)

    async def usergen_has_value(self, name: str, value: str) -> bool:
        if name == "plot":
            table_plot = "creative_plot"
            table_wp = "creative_wp"
            plot_value = await self._conn.fetchval(
                q.get_creative_by_value.format(table_plot),
                value,
            )
            wp_value = await self._conn.fetchval(
                q.get_creative_by_value.format(table_wp),
                value,
            )
            plot_unchecked_value = await self._conn.fetchval(
                "SELECT value FROM creative_unchecked WHERE name = $1 AND value iLIKE $2;",
                name,
                value,
            )
            plot_invalid_value = await self._conn.fetchval(
                "SELECT value FROM creative_invalid WHERE name = $1 AND value iLIKE $2;",
                name,
                value,
            )
            return (
                plot_value is not None
                or wp_value is not None
                or plot_unchecked_value is not None
                or plot_invalid_value is not None
            )

        table = f"creative_{name}"
        actual_value = await self._conn.fetchval(
            q.get_creative_by_value.format(table),
            value,
        )
        unchecked_value = await self._conn.fetchval(
            "SELECT value FROM creative_unchecked WHERE name = $1 AND value iLIKE $2;",
            name,
            value,
        )
        invalid_value = await self._conn.fetchval(
            "SELECT value FROM creative_invalid WHERE name = $1 AND value iLIKE $2;",
            name,
            value,
        )
        return (
            actual_value is not None
            or unchecked_value is not None
            or invalid_value is not None
        )

    async def suggest(self, data: dict) -> None:
        name = data.get("name")
        value = data.get("value")
        await self._conn.execute(q.suggest, name, value)

    async def get_first_unchecked_usergen(self) -> Optional[dict]:
        return dict_or_none(await self._conn.fetchrow(q.get_first_unchecked_usergen))

    async def get_unchecked_usergen_count(self) -> int:
        return await self._conn.fetchval("SELECT COUNT(*) FROM creative_unchecked")  # type: ignore

    async def get_first_unchecked_wp(self) -> Optional[dict]:
        return dict_or_none(await self._conn.fetchrow(q.get_first_unchecked_wp))

    async def get_unchecked_wp_count(self) -> int:
        return await self._conn.fetchval("SELECT COUNT(*) FROM creative_wp_unchecked")  # type: ignore

    async def _all_similar_values(self, name: str, value: str) -> List[str]:
        table = f"creative_{name}"
        return [
            f"{row.get('value')} - {row.get('similarity')}"
            for row in await self._conn.fetch(
                f"SELECT *, similarity('{value}', value) as similarity FROM {table} WHERE similarity('{value}', value) > {SIMILARITY};"
            )
        ]

    async def _all_similar_values_in_invalid(self, name: str, value: str) -> List[str]:
        return [
            f"{row.get('value')} - {row.get('similarity')}"
            for row in await self._conn.fetch(
                f"SELECT *, similarity('{value}', value) as similarity FROM creative_invalid WHERE name = $1 AND similarity('{value}', value) > {SIMILARITY};",
                name,
            )
        ]

    async def get_similar_usergen(self, name: str, value: str) -> List[dict]:
        if name == "plot":
            wp_actual = await self._all_similar_values("wp", value)
            wp_invalid = await self._all_similar_values("wp_invalid", value)
            plot_actual = await self._all_similar_values("plot", value)
            plot_invalid = await self._all_similar_values_in_invalid("plot", value)
            valid = [{"value": v, "valid": True} for v in [*plot_actual, *wp_actual]]
            invalid = [
                {"value": v, "valid": False} for v in [*plot_invalid, *wp_invalid]
            ]
            return [
                *valid,
                *invalid,
            ]

        actual = [
            {"value": v, "valid": True}
            for v in await self._all_similar_values(name, value)
        ]
        invalid = [
            {"value": v, "valid": False}
            for v in await self._all_similar_values_in_invalid(name, value)
        ]
        return [*actual, *invalid]

    async def check(self, data: dict) -> None:
        unchecked_id = data.get("id")
        name = data.get("name")
        value = data.get("value")
        valid = data.get("valid")
        async with self._conn.transaction():
            await self._conn.execute(
                "DELETE FROM creative_unchecked WHERE id = $1;", unchecked_id
            )
            if valid:
                actual_id = await self._conn.fetchval(
                    f"INSERT INTO creative_{name} (value) VALUES ($1) RETURNING id;",
                    value,
                )
                await self._conn.execute(
                    "INSERT INTO creative_unchecked_actual_invalid (name, unchecked_id, actual_id) VALUES ($1, $2, $3);",
                    name,
                    unchecked_id,
                    actual_id,
                )
                reset_meta(name)
            else:
                invalid_id = await self._conn.fetchval(
                    "INSERT INTO creative_invalid (name, value) VALUES ($1, $2) RETURNING id;",
                    name,
                    value,
                )
                await self._conn.execute(
                    "INSERT INTO creative_unchecked_actual_invalid (name, unchecked_id, invalid_id) VALUES ($1, $2, $3);",
                    name,
                    unchecked_id,
                    invalid_id,
                )

    async def check_wp(self, data: dict) -> None:
        unchecked_id = data.get("id")
        value = data.get("value")
        english = data.get("english")
        valid = data.get("valid")
        async with self._conn.transaction():
            await self._conn.execute(
                "DELETE FROM creative_wp_unchecked WHERE id = $1;", unchecked_id
            )
            if valid:
                actual_id = await self._conn.fetchval(
                    "INSERT INTO creative_wp (value, english) VALUES ($1, $2) RETURNING id;",
                    value,
                    english,
                )
                await self._conn.execute(
                    "INSERT INTO creative_wp_unchecked_actual_invalid (unchecked_id, actual_id) VALUES ($1, $2);",
                    unchecked_id,
                    actual_id,
                )
                reset_meta("wp")
            else:
                invalid_id = await self._conn.fetchval(
                    "INSERT INTO creative_wp_invalid (value, english) VALUES ($1, $2) RETURNING id;",
                    value,
                    english,
                )
                await self._conn.execute(
                    "INSERT INTO creative_wp_unchecked_actual_invalid (unchecked_id, invalid_id) VALUES ($1, $2);",
                    unchecked_id,
                    invalid_id,
                )

    async def uncheck_actual(self, name: str, actual_id: int) -> None:
        async with self._conn.transaction():
            unchecked_id = await self._conn.fetchval(
                "SELECT unchecked_id FROM creative_unchecked_actual_invalid WHERE name = $1 AND actual_id = $2;",
                name,
                actual_id,
            )
            if unchecked_id is None:
                return None

            await self._conn.execute(
                "DELETE FROM creative_unchecked_actual_invalid WHERE name = $1 AND actual_id = $2;",
                name,
                actual_id,
            )
            actual_value = await self._conn.fetchval(
                f"SELECT value FROM creative_{name} WHERE id = $1;", actual_id
            )
            await self._conn.execute(
                f"DELETE FROM creative_{name} WHERE id = $1;", actual_id
            )
            await self._conn.execute(
                "INSERT INTO creative_unchecked(id, name, value) VALUES ($1, $2, $3)",
                unchecked_id,
                name,
                actual_value,
            )
            reset_meta(name)

    async def uncheck_actual_wp(self, actual_id: int) -> None:
        async with self._conn.transaction():
            unchecked_id = await self._conn.fetchval(
                "SELECT unchecked_id FROM creative_wp_unchecked_actual_invalid WHERE actual_id = $1;",
                actual_id,
            )
            if unchecked_id is None:
                return None

            await self._conn.execute(
                "DELETE FROM creative_wp_unchecked_actual_invalid WHERE actual_id = $1;",
                actual_id,
            )
            actual_row = await self._conn.fetchrow(
                "SELECT value, english FROM creative_wp WHERE id = $1;", actual_id
            )
            actual_value = actual_row.get("value")
            actual_english = actual_row.get("english")

            await self._conn.execute(
                "DELETE FROM creative_wp WHERE id = $1;", actual_id
            )
            await self._conn.execute(
                "INSERT INTO creative_wp_unchecked(id, value, english) VALUES ($1, $2, $3)",
                unchecked_id,
                actual_value,
                actual_english,
            )
            reset_meta("wp")

    async def uncheck_invalid(self, name: str, invalid_id: int) -> None:
        async with self._conn.transaction():
            unchecked_id = await self._conn.fetchval(
                "SELECT unchecked_id FROM creative_unchecked_actual_invalid WHERE name = $1 AND invalid_id = $2;",
                name,
                invalid_id,
            )
            if unchecked_id is None:
                return None

            await self._conn.execute(
                "DELETE FROM creative_unchecked_actual_invalid WHERE name = $1 AND invalid_id = $2",
                name,
                invalid_id,
            )
            invalid_value = await self._conn.fetchval(
                "SELECT value FROM creative_invalid WHERE id = $1;", invalid_id
            )
            await self._conn.execute(
                "DELETE FROM creative_invalid WHERE id = $1;", invalid_id
            )
            await self._conn.execute(
                "INSERT INTO creative_unchecked(id, name, value) VALUES ($1, $2, $3)",
                unchecked_id,
                name,
                invalid_value,
            )

    async def uncheck_invalid_wp(self, invalid_id: int) -> None:
        async with self._conn.transaction():
            unchecked_id = await self._conn.fetchval(
                "SELECT unchecked_id FROM creative_wp_unchecked_actual_invalid WHERE invalid_id = $1;",
                invalid_id,
            )
            if unchecked_id is None:
                return None

            await self._conn.execute(
                "DELETE FROM creative_wp_unchecked_actual_invalid WHERE invalid_id = $1;",
                invalid_id,
            )
            invalid_row = await self._conn.fetchrow(
                "SELECT value, english FROM creative_wp_invalid WHERE id = $1;",
                invalid_id,
            )
            invalid_value = invalid_row.get("value")
            invalid_english = invalid_row.get("english")
            await self._conn.execute(
                "DELETE FROM creative_wp_invalid WHERE id = $1;", invalid_id
            )
            await self._conn.execute(
                "INSERT INTO creative_wp_unchecked(id, value, english) VALUES ($1, $2, $3)",
                unchecked_id,
                invalid_value,
                invalid_english,
            )

    async def get_last_checked_usergen(self, count: int) -> List[dict]:
        rows = await self._conn.fetch(
            "SELECT * FROM creative_unchecked_actual_invalid ORDER BY id DESC LIMIT $1;",
            count,
        )

        res = []
        for row in rows:
            name = row.get("name")
            # unchecked_id = row.get("unchecked_id")
            actual_id = row.get("actual_id")
            invalid_id = row.get("invalid_id")
            valid = actual_id is not None
            if valid:
                s = await self._conn.fetchrow(
                    f"SELECT * FROM creative_{name} WHERE id = $1;",
                    actual_id,
                )
                s = dict(s)
                s["name"] = name
                s["valid"] = True
            else:
                s = await self._conn.fetchrow(
                    "SELECT * FROM creative_invalid WHERE id = $1;",
                    invalid_id,
                )
                s = dict(s)
                s["name"] = name
                s["valid"] = False

            res.append(s)

        return res

    async def get_last_checked_wp(self, count: int) -> List[dict]:
        rows = await self._conn.fetch(
            "SELECT * FROM creative_wp_unchecked_actual_invalid ORDER BY id DESC LIMIT $1;",
            count,
        )

        res = []
        for row in rows:
            actual_id = row.get("actual_id")
            invalid_id = row.get("invalid_id")
            valid = actual_id is not None
            if valid:
                s = await self._conn.fetchrow(
                    "SELECT * FROM creative_wp WHERE id = $1;",
                    actual_id,
                )
                s = dict(s)
                s["valid"] = True
            else:
                s = await self._conn.fetchrow(
                    "SELECT * FROM creative_wp_invalid WHERE id = $1;",
                    invalid_id,
                )
                s = dict(s)
                s["valid"] = False

            res.append(s)

        return res

    async def _count_valid(self, name: str) -> int:
        return await self._conn.fetchval(f"SELECT COUNT(1) FROM creative_{name}")  # type: ignore

    async def _count_unchecked(self, name: str) -> int:
        return await self._conn.fetchval(  # type: ignore
            "SELECT COUNT(1) FROM creative_unchecked WHERE name = $1",
            name,
        )

    async def _count_wp_unchecked(self) -> int:
        return await self._conn.fetchval("SELECT COUNT(1) FROM creative_wp_unchecked")  # type: ignore

    async def get_stats(self) -> dict:
        keys = [
            "awkward_moment",
            "bookname",
            "crowd",
            "motivation",
            "plot",
        ]
        valid = {}
        for key in keys:
            valid[key] = await self._count_valid(key)
        valid["wp"] = await self._count_valid("wp")

        unchecked = {}
        for key in keys:
            unchecked[key] = await self._count_unchecked(key)
        unchecked["wp"] = await self._count_wp_unchecked()

        return {"valid": valid, "unchecked": unchecked}
