from abc import ABC, abstractmethod
from typing import Generic, List, Optional, TypeVar

from app.domain.entities.connection import ConnectionConfig
from app.domain.entities.masking_job import MaskingJob
from app.domain.entities.masking_rule import MaskingRule
from app.domain.entities.user import User
from app.domain.entities.audit_log import AuditLog

T = TypeVar("T")


class Repository(ABC, Generic[T]):
    @abstractmethod
    async def create(self, entity: T) -> T:
        pass

    @abstractmethod
    async def get_by_id(self, id: str) -> Optional[T]:
        pass

    @abstractmethod
    async def get_all(self) -> List[T]:
        pass

    @abstractmethod
    async def update(self, id: str, entity: T) -> Optional[T]:
        pass

    @abstractmethod
    async def delete(self, id: str) -> bool:
        pass


class ConnectionRepository(Repository[ConnectionConfig], ABC):
    pass


class RuleRepository(Repository[MaskingRule], ABC):
    pass


class JobRepository(Repository[MaskingJob], ABC):
    pass


class AuditLogRepository(Repository[AuditLog], ABC):
    @abstractmethod
    async def get_by_job_id(self, job_id: str) -> List[AuditLog]:
        pass


class UserRepository(Repository[User], ABC):
    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[User]:
        pass
