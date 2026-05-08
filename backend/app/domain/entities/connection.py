from enum import Enum
from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any

from app.domain.value_objects.database_type import DatabaseType


class ConnectionConfig(BaseModel):
    id: Optional[str] = None
    name: str
    type: DatabaseType
    host: str
    port: int
    database: str
    username: str
    password: str
    additional_options: Optional[Dict[str, Any]] = None
    owner_id: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


Connection = ConnectionConfig
