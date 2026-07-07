from typing import Optional

from pydantic import BaseModel


class AccessTokenPayload(BaseModel):
    sub: str
    username: str
    tg_id: Optional[int] = None
    exp: int  # timestamp expires
