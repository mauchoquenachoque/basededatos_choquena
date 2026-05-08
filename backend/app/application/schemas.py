from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from app.domain.value_objects.database_type import DatabaseType
from app.domain.value_objects.masking_algorithm import MaskingAlgorithm
from app.domain.entities.masking_job import JobStatus
from datetime import datetime

class ConnectionCreate(BaseModel):
    name: str
    type: DatabaseType
    host: str
    port: int
    database: str
    username: str
    password: str
    additional_options: Optional[Dict[str, Any]] = None

class ConnectionResponse(ConnectionCreate):
    id: str

class RuleCreate(BaseModel):
    name: str
    connection_id: str
    target_table: str
    target_column: str
    strategy: MaskingAlgorithm
    strategy_options: Optional[Dict[str, Any]] = None

class RuleResponse(RuleCreate):
    id: str

class JobCreate(BaseModel):
    connection_id: str
    rule_ids: List[str]

class JobResponse(BaseModel):
    id: str
    connection_id: str
    rule_ids: List[str]
    status: JobStatus
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    records_processed: int
    shared_with: List[str] = Field(default_factory=list)

class JobShareRequest(BaseModel):
    email: EmailStr

class AuditLogEntry(BaseModel):
    id: str
    job_id: str
    user_id: str
    user_email: str
    user_role: str
    action: str
    is_masked: bool
    timestamp: datetime

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=256)
    name: str = Field(min_length=1, max_length=120)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=256)


class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    role: str
    picture: Optional[str] = None

class AuthResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class DynamicQueryResponse(BaseModel):
    data: List[Dict[str, Any]]
    total_records: int
    is_masked: bool
