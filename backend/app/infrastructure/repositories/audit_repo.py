import uuid
from typing import Any, Dict, List, Optional
import motor.motor_asyncio

from app.domain.entities.audit_log import AuditLog
from app.domain.interfaces.repository import AuditLogRepository


class MongoAuditRepository(AuditLogRepository):
    def __init__(self, uri: str, metadata_database: str = "enmask_meta"):
        self.client = motor.motor_asyncio.AsyncIOMotorClient(uri)
        self.db = self.client[metadata_database]
        self.collection = self.db["audit_logs"]

    async def _serialize(self, entity: AuditLog) -> Dict[str, Any]:
        return entity.model_dump(mode="json")

    async def create(self, entity: AuditLog) -> AuditLog:
        entity_dict = await self._serialize(entity)
        entity_dict["id"] = entity_dict.get("id") or str(uuid.uuid4())
        await self.collection.insert_one(entity_dict)
        return AuditLog(**entity_dict)

    async def get_by_id(self, id: str) -> Optional[AuditLog]:
        data = await self.collection.find_one({"id": id})
        if not data:
            return None
        return AuditLog(**data)

    async def get_all(self) -> List[AuditLog]:
        results = []
        cursor = self.collection.find({}).sort("timestamp", -1)
        async for doc in cursor:
            results.append(AuditLog(**doc))
        return results

    async def get_by_job_id(self, job_id: str) -> List[AuditLog]:
        results = []
        cursor = self.collection.find({"job_id": job_id}).sort("timestamp", -1)
        async for doc in cursor:
            results.append(AuditLog(**doc))
        return results

    async def update(self, id: str, entity: AuditLog) -> Optional[AuditLog]:
        entity_dict = await self._serialize(entity)
        result = await self.collection.update_one({"id": id}, {"$set": entity_dict})
        if result.modified_count:
            return AuditLog(**entity_dict)
        return None

    async def delete(self, id: str) -> bool:
        result = await self.collection.delete_one({"id": id})
        return result.deleted_count == 1
