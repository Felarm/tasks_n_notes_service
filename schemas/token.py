from typing import Optional

from pydantic import BaseModel


class AccessTokenPayload(BaseModel):
    sub: str
    username: str
    tg_id: Optional[int] = None
    exp: int  # timestamp expires
    iat: int  # timestamp issued at
    type: str = "access"
    jti: str


class ServiceTokenPayload(BaseModel):
    sub: str
    username: str
    type: str = "service"
