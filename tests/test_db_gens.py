import pytest

from asyncpg import Connection
from fastapi_auth import User

from app.db.postgres.gens import GensExt

from app.core.head import Head
from app.core.metadata import Metadata


pytestmark = pytest.mark.anyio


@pytest.fixture
def gens_ext(db_conn: Connection):
    return GensExt(db_conn)


@pytest.fixture
def valid_head():
    return Head(
        title="title1",
        description="description1",
        access=0,
        category="Игры",
        subcategories=["Другое"],
        tags=["tag1"],
    )


@pytest.fixture
def valid_metadata():
    return Metadata()


async def test_get_none(gens_ext: GensExt):
    item = await gens_ext.get(99999)
    assert item is None


async def test_create(
    gens_ext: GensExt,
    model_user_admin: User,
    valid_head: Head,
    valid_metadata: Metadata,
):
    id = await gens_ext.create(
        model_user_admin,
        valid_head,
        {},
        {},
        valid_metadata,
    )
    assert id == 1


# TODO: not working
# async def test_update(
#     gens_ext: GensExt,
#     model_user_admin: User,
#     valid_head: Head,
#     valid_metadata: dict,
# ):
#     id = await gens_ext.create(
#         model_user_admin,
#         valid_head,
#         {},
#         {},
#         valid_metadata,
#     )
#     res = await gens_ext.update(
#         id,
#         model_user_admin,
#         valid_head,
#         {},
#         {},
#         valid_metadata,
#     )
#     assert res
