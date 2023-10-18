from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterable

import jwt
from fastapi_auth.backend.abc.jwt import AbstractJWTBackend
from fastapi_auth.errors import TokenDecodingError


class Algorithm:
    def __init__(
        self,
        kid: str,
        algorithm: str,
        private_key: Any,
        public_key: Any,
        main: bool = False,
    ) -> None:
        self.kid = kid
        self.algorithm = algorithm
        self.private_key = private_key
        self.public_key = public_key
        self.main = main


class JWTMultiBackend(AbstractJWTBackend):
    def __init__(self, methods: Iterable[Algorithm], fallback_kid: str):
        self._algorithms: Dict[str, Algorithm] = {}
        for method in methods:
            self._algorithms[method.kid] = method
            if method.main:
                self._main = method

        if not hasattr(self, "_main"):
            raise Exception("no main algorithm")

        self._fallback_kid = fallback_kid

    def create_token(
        self,
        type: str,
        payload: dict,
        expiration: int,
    ) -> str:
        iat = datetime.now(timezone.utc)
        exp = iat + timedelta(seconds=expiration)

        headers = {
            "kid": self._main.kid,
        }

        payload.update(
            {
                "type": type,
                "iat": iat,
                "exp": exp,
            }
        )

        return jwt.encode(
            payload,
            self._main.private_key,
            algorithm=self._main.algorithm,
            headers=headers,
        )

    def decode_token(self, token: str) -> dict:
        if token:
            try:
                header = jwt.get_unverified_header(token)
                received_kid = header.get("kid")
                if received_kid is not None:
                    kid = received_kid
                else:
                    kid = self._fallback_kid

                algorithm = self._algorithms.get(kid)
                assert algorithm is not None
                payload = jwt.decode(
                    token,
                    algorithm.public_key,
                    algorithms=[algorithm.algorithm],
                )
                payload.update(header)
                if received_kid is None:
                    permissions = payload.get("permissions")
                    if permissions is not None:
                        payload["roles"] = permissions
                    else:
                        # just in case
                        payload["roles"] = []
                return payload
            except Exception:
                pass

        raise TokenDecodingError
