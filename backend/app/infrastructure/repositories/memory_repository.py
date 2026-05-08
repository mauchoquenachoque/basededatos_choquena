import uuid
from typing import List, Optional, TypeVar, Dict
from app.domain.interfaces.repository import Repository
from pydantic import BaseModel

T = TypeVar('T', bound=BaseModel)

class MemoryRepository(Repository[T]):
    def __init__(self):
        self._data: Dict[str, T] = {}

    async def create(self, entity: T) -> T:
        entity_dict = entity.model_dump()
        if not entity_dict.get("id"):
            entity_dict["id"] = str(uuid.uuid4())
        
        # We need to recreate the entity with the new ID
        new_entity = entity.__class__(**entity_dict)
        self._data[new_entity.id] = new_entity
        return new_entity

    async def get_by_id(self, id: str) -> Optional[T]:
        return self._data.get(id)

    async def get_all(self) -> List[T]:
        return list(self._data.values())

    async def update(self, id: str, entity: T) -> Optional[T]:
        if id in self._data:
            entity_dict = entity.model_dump()
            entity_dict["id"] = id
            updated_entity = entity.__class__(**entity_dict)
            self._data[id] = updated_entity
            return updated_entity
        return None

    async def delete(self, id: str) -> bool:
        if id in self._data:
            del self._data[id]
            return True
        return False

# Global instances for simple dependency injection in this non-DB backed setup
from app.domain.entities.connection import ConnectionConfig
from app.domain.entities.masking_rule import MaskingRule
from app.domain.entities.masking_job import MaskingJob

connection_repository = MemoryRepository[ConnectionConfig]()
rule_repository = MemoryRepository[MaskingRule]()
job_repository = MemoryRepository[MaskingJob]()
