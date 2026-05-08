from typing import Optional
from app.domain.entities.user import User
from app.infrastructure.repositories.memory_repository import MemoryRepository


class UserRepository(MemoryRepository[User]):
    async def get_by_email(self, email: str) -> Optional[User]:
        normalized_email = email.strip().lower()
        return next(
            (user for user in self._data.values() if user.email.strip().lower() == normalized_email),
            None,
        )


user_repository = UserRepository()
