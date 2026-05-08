import json
import uuid
from typing import List, Optional

import motor.motor_asyncio

from app.domain.entities.connection import ConnectionConfig
from app.domain.interfaces.repository import ConnectionRepository


class MongoDBConnectionRepository(ConnectionRepository):
    def __init__(self, uri: str, metadata_database: str = "enmask_meta"):
        self.client = motor.motor_asyncio.AsyncIOMotorClient(uri)
        self.db = self.client[metadata_database]
        self.collection = self.db["connections"]

    async def create(self, entity: ConnectionConfig) -> ConnectionConfig:
        entity_dict = entity.model_dump(mode="json")
        entity_dict["id"] = entity_dict.get("id") or str(uuid.uuid4())
        db_doc = entity_dict.copy()
        db_doc["additional_options"] = json.dumps(db_doc.get("additional_options") or {})
        await self.collection.insert_one(db_doc)
        return ConnectionConfig(**entity_dict)

    async def get_by_id(self, id: str) -> Optional[ConnectionConfig]:
        data = await self.collection.find_one({"id": id})
        if not data:
            return None
        try:
            raw_options = data.get("additional_options")
            data["additional_options"] = json.loads(raw_options) if raw_options else {}
            return ConnectionConfig(**data)
        except Exception:
            return None

    async def get_all(self) -> List[ConnectionConfig]:
        cursor = self.collection.find({})
        records = []
        async for doc in cursor:
            try:
                raw_options = doc.get("additional_options")
                doc["additional_options"] = json.loads(raw_options) if raw_options else {}
                records.append(ConnectionConfig(**doc))
            except Exception as e:
                print(f"Skipping invalid connection record {doc.get('id', 'unknown')}: {e}")
        return records

    async def update(self, id: str, entity: ConnectionConfig) -> Optional[ConnectionConfig]:
        entity_dict = entity.model_dump(mode="json")
        db_doc = entity_dict.copy()
        db_doc["additional_options"] = json.dumps(db_doc.get("additional_options") or {})
        result = await self.collection.update_one({"id": id}, {"$set": db_doc})
        if result.modified_count:
            return ConnectionConfig(**entity_dict)
        return None

    async def delete(self, id: str) -> bool:
        result = await self.collection.delete_one({"id": id})
        return result.deleted_count == 1
