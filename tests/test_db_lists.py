import pytest

from asyncpg import Connection

from app.db.postgres.lists import ListsExt
from fastapi_auth import User


pytestmark = pytest.mark.anyio


@pytest.fixture
def lists_ext(db_conn: Connection):
    return ListsExt(db_conn)


@pytest.fixture
def valid_data():
    return {
        "title": "title1",
        "description": "description1",
        "access": 0,
        "content": "content1",
        "slicer": 1,
    }


async def test_get_none(lists_ext: ListsExt):
    item = await lists_ext.get(99999)
    assert item is None


async def test_create(
    lists_ext: ListsExt,
    model_user_admin: User,
    valid_data: dict,
):
    id = await lists_ext.create(model_user_admin, valid_data)
    assert id == 1

    item = await lists_ext.get(id)
    assert item is not None
    assert item.get("id") == id
    assert item.get("title") == valid_data.get("title")
    assert item.get("description") == valid_data.get("description")
    assert item.get("active") is True


async def test_update_owner(
    lists_ext: ListsExt,
    model_user_admin: User,
    valid_data: dict,
):
    valid_data["title"] = "title1update"
    id = await lists_ext.create(model_user_admin, valid_data)
    res = await lists_ext.update(id, model_user_admin, valid_data)
    assert res is True

    item = await lists_ext.get(id)
    assert item.get("title") == valid_data.get("title")


async def test_activate_deactivate(
    lists_ext: ListsExt,
    model_user_admin: User,
    valid_data: dict,
):
    id = await lists_ext.create(model_user_admin, valid_data)

    await lists_ext.deactivate(id)
    item = await lists_ext.get(id)
    assert item.get("active") is False

    await lists_ext.activate(id)
    item = await lists_ext.get(id)
    assert item.get("active") is True
