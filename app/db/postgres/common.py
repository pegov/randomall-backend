from typing import List, Optional


def was_updated(v: str) -> bool:
    return v != "UPDATE 0"


def was_deleted(v: str) -> bool:
    return v != "DELETE 0"


def dict_or_none(v) -> Optional[dict]:
    if v is not None:
        return dict(v)

    return None


def fix_user_field(items: List[dict]) -> List[dict]:
    return [
        dict(
            **row,
            user={
                "id": row.get("user_id"),
                "username": row.get("username"),
            }
        )
        for row in items
    ]


def get_offset(size: int, page: int) -> int:
    return size * (page - 1)


def get_pages(count: int, size: int) -> int:
    div = count // size
    return div if count % size == 0 else div + 1
