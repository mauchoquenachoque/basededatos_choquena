from typing import List, Dict, Any
from motor.motor_asyncio import AsyncIOMotorClient
from app.domain.interfaces.vault_repository import VaultRepository

class MemoryVaultRepository(VaultRepository):
    def __init__(self):
        # job_id -> list of backup records
        self._data: Dict[str, List[Dict[str, Any]]] = {}

    async def save_backup(self, job_id: str, table_name: str, record_pk: str, original_data: Dict[str, Any]) -> None:
        if job_id not in self._data:
            self._data[job_id] = []
        
        self._data[job_id].append({
            "job_id": job_id,
            "table_name": table_name,
            "record_pk": record_pk,
            "original_data": original_data
        })

    async def get_backups_for_job(self, job_id: str) -> List[Dict[str, Any]]:
        return self._data.get(job_id, [])

    async def delete_backups_for_job(self, job_id: str) -> None:
        if job_id in self._data:
            del self._data[job_id]


class MongoVaultRepository(VaultRepository):
    def __init__(self, uri: str, database_name: str):
        self.client = AsyncIOMotorClient(uri)
        self.db = self.client[database_name]
        self.collection = self.db["vault_backups"]

    async def save_backup(self, job_id: str, table_name: str, record_pk: str, original_data: Dict[str, Any]) -> None:
        doc = {
            "job_id": job_id,
            "table_name": table_name,
            "record_pk": record_pk,
            "original_data": original_data
        }
        # Insert without updating, or update if exists? We assume a new backup.
        # But to be safe from multiple runs, maybe we could upsert.
        # For simplicity, we just insert.
        await self.collection.insert_one(doc)

    async def get_backups_for_job(self, job_id: str) -> List[Dict[str, Any]]:
        cursor = self.collection.find({"job_id": job_id})
        results = []
        async for document in cursor:
            # remove _id from results to avoid serialization issues
            if "_id" in document:
                del document["_id"]
            results.append(document)
        return results

    async def delete_backups_for_job(self, job_id: str) -> None:
        await self.collection.delete_many({"job_id": job_id})

# Initialize memory fallback instance
memory_vault_repository = MemoryVaultRepository()
