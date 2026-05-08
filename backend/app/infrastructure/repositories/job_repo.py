import json
import uuid
from typing import Any, Dict, List, Optional

import motor.motor_asyncio
from pydantic import BaseModel

from app.domain.entities.masking_job import MaskingJob
from app.domain.interfaces.repository import JobRepository


class MongoJobRepository(JobRepository):
    def __init__(self, uri: str, metadata_database: str = "enmask_meta"):
        self.client = motor.motor_asyncio.AsyncIOMotorClient(uri)
        self.db = self.client[metadata_database]
        self.collection = self.db["jobs"]

    async def _serialize(self, entity: MaskingJob) -> Dict[str, Any]:
        return entity.model_dump(mode="json")

    async def create(self, entity: MaskingJob) -> MaskingJob:
        entity_dict = await self._serialize(entity)
        entity_dict["id"] = entity_dict.get("id") or str(uuid.uuid4())
        await self.collection.insert_one(entity_dict)
        return MaskingJob(**entity_dict)

    async def get_by_id(self, id: str) -> Optional[MaskingJob]:
        data = await self.collection.find_one({"id": id})
        if not data:
            return None
        try:
            return MaskingJob(**data)
        except Exception:
            return None

    async def get_all(self) -> List[MaskingJob]:
        results = []
        cursor = self.collection.find({})
        async for doc in cursor:
            try:
                results.append(MaskingJob(**doc))
            except Exception as e:
                print(f"Skipping invalid job record {doc.get('id', 'unknown')}: {e}")
        return results

    async def update(self, id: str, entity: MaskingJob) -> Optional[MaskingJob]:
        entity_dict = await self._serialize(entity)
        result = await self.collection.update_one({"id": id}, {"$set": entity_dict})
        if result.modified_count:
            return MaskingJob(**entity_dict)
        return None

    async def delete(self, id: str) -> bool:
        result = await self.collection.delete_one({"id": id})
        return result.deleted_count == 1
