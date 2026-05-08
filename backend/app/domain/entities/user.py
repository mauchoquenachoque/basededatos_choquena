from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class User(BaseModel):
    id: Optional[str] = None
    email: str
    name: str
    role: Literal["admin", "user"] = "user"
    picture: Optional[str] = None
    password_hash: Optional[str] = Field(default=None, repr=False)

    model_config = ConfigDict(from_attributes=True)
