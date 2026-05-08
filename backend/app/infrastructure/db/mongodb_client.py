import motor.motor_asyncio
from typing import List, Dict, Any
from urllib.parse import quote_plus


def build_mongo_uri(host: str, username: str, password: str, port: int | None = None) -> str:
    host = host.strip()
    enc_user = quote_plus(username)
    enc_pass = quote_plus(password)

    if host.startswith("mongodb+srv://") or host.startswith("mongodb://"):
        scheme, endpoint = host.split("://", 1)
        return f"{scheme}://{enc_user}:{enc_pass}@{endpoint}"

    if host.endswith(".mongodb.net"):
        return f"mongodb+srv://{enc_user}:{enc_pass}@{host}"

    if ":" in host:
        return f"mongodb://{enc_user}:{enc_pass}@{host}"

    if port:
        return f"mongodb://{enc_user}:{enc_pass}@{host}:{port}"

    return f"mongodb://{enc_user}:{enc_pass}@{host}"


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
