from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class AuditLog(BaseModel):
    id: Optional[str] = None
    job_id: str
    user_id: str
    user_email: str
    user_role: str
    action: str = "query"
    is_masked: bool
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)
