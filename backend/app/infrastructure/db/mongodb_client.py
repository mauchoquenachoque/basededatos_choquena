import motor.motor_asyncio
from typing import List, Dict, Any

class MongoClient:
    def __init__(self, uri: str, database: str):
        self.client = motor.motor_asyncio.AsyncIOMotorClient(uri)
        self.db = self.client[database]

    async def fetch_all(self, collection_name: str, query: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        query = query or {}
        collection = self.db[collection_name]
        cursor = collection.find(query)
        records = await cursor.to_list(length=None)
        # convert ObjectId to string safely
        for r in records:
            if "_id" in r:
                r["_id"] = str(r["_id"])
        return records

    async def update_record(self, collection_name: str, record_id: Any, updates: Dict[str, Any]):
        from bson import ObjectId
        collection = self.db[collection_name]
        # Allow _id to be either string or ObjectId depending on how it was passed
        try:
            query_id = ObjectId(record_id) if isinstance(record_id, str) and len(record_id) == 24 else record_id
        except Exception:
            query_id = record_id
            
        await collection.update_one({"_id": query_id}, {"$set": updates})

    async def get_schema(self) -> Dict[str, List[str]]:
        collections = await self.db.list_collection_names()
        schema = {}
        for coll_name in collections:
            collection = self.db[coll_name]
            doc = await collection.find_one({})
            if doc:
                keys = [k for k in doc.keys() if k != "_id"]
                schema[coll_name] = keys
            else:
                schema[coll_name] = []
        return schema
