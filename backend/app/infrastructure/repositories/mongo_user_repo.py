import uuid
from typing import Any, Dict, List, Optional
import motor.motor_asyncio

from app.domain.entities.user import User
from app.domain.interfaces.repository import UserRepository


class MongoUserRepository(UserRepository):
    def __init__(self, uri: str, metadata_database: str = "enmask_meta"):
        self.client = motor.motor_asyncio.AsyncIOMotorClient(uri)
        self.db = self.client[metadata_database]
        self.collection = self.db["users"]

    async def _serialize(self, entity: User) -> Dict[str, Any]:
        data = entity.model_dump(mode="json")
        return data

    async def create(self, entity: User) -> User:
        entity_dict = await self._serialize(entity)
        entity_dict["id"] = entity_dict.get("id") or str(uuid.uuid4())
        await self.collection.insert_one(entity_dict)
        return User(**entity_dict)

    async def get_by_id(self, id: str) -> Optional[User]:
        data = await self.collection.find_one({"id": id})
        if not data:
            return None
        return User(**data)

    async def get_by_email(self, email: str) -> Optional[User]:
        normalized_email = email.strip().lower()
        data = await self.collection.find_one({"email": normalized_email})
        if not data:
            return None
        return User(**data)

    async def get_all(self) -> List[User]:
        results = []
        cursor = self.collection.find({})
        async for doc in cursor:
            results.append(User(**doc))
        return results

    async def update(self, id: str, entity: User) -> Optional[User]:
        entity_dict = await self._serialize(entity)
        result = await self.collection.update_one({"id": id}, {"$set": entity_dict})
        if result.modified_count:
            return User(**entity_dict)
        return None

    async def delete(self, id: str) -> bool:
        result = await self.collection.delete_one({"id": id})
        return result.deleted_count == 1
