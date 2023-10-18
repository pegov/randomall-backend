import orjson


def obj_to_json_str(obj: dict) -> str:
    return orjson.dumps(obj).decode()
