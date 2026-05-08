from typing import List, Dict, Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncConnection, create_async_engine


class PostgresClient:
    def __init__(self, dsn: str):
        self.engine: AsyncEngine = create_async_engine(dsn, future=True, echo=False, pool_pre_ping=True)

    async def fetch_all(self, query: str, *args) -> List[Dict[str, Any]]:
        async with self.engine.connect() as conn:
            result = await conn.execute(text(query), *args)
            return [dict(row) for row in result.mappings().all()]

    async def execute(self, query: str, *args) -> str:
        async with self.engine.connect() as conn:
            result = await conn.execute(text(query), *args)
            await conn.commit()
            return str(result)

    async def update_record(self, table: str, record_id_col: str, record_id: Any, updates: Dict[str, Any]):
        set_clause = ", ".join([f"{column} = :{column}" for column in updates.keys()])
        parameters = {**updates, "record_id": record_id}
        query = text(f"UPDATE {table} SET {set_clause} WHERE {record_id_col} = :record_id")
        async with self.engine.connect() as conn:
            await conn.execute(query, parameters)
            await conn.commit()

    async def get_schema(self) -> Dict[str, List[str]]:
        query = """
            SELECT table_name, column_name 
            FROM information_schema.columns 
            WHERE table_schema = 'public'
        """
        records = await self.fetch_all(query)
        schema = {}
        for record in records:
            t = record["table_name"]
            c = record["column_name"]
            if t not in schema:
                schema[t] = []
            schema[t].append(c)
        return schema

