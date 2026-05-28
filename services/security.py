from datetime import datetime, UTC

from jose import jwt, JWTError

from config import settings
from exceptions import UnauthorizedException
from schemas.token import AccessTokenPayload, ServiceTokenPayload


class JWTService:
    @staticmethod
    def get_access_token_payload(encoded_token: str) -> AccessTokenPayload:
        try:
            payload = AccessTokenPayload(**jwt.decode(encoded_token, settings.SECRET_KEY, settings.ALGORITHM))
        except JWTError as e:
            raise UnauthorizedException("Wrong token data") from e
        if payload.type != "access":
            raise UnauthorizedException("Wrong token type")
        if payload.exp < int(datetime.now(UTC).timestamp()):
            raise UnauthorizedException("Expired token")
        return payload