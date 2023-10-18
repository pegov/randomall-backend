import hashlib

import orjson

from app.core.abc import AbstractEngine


class HashMiddleware:
    def __call__(self, engine: AbstractEngine, **kwargs) -> None:
        bytes_to_hash = orjson.dumps(engine.body_raw.get("blocks"))  # type: ignore
        hash_ = hashlib.sha1(bytes_to_hash).hexdigest()
        engine.metadata.hash = hash_
