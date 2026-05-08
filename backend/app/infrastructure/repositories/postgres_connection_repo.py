import json
import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from app.core.config import settings
from app.domain.entities.connection import ConnectionConfig
from app.domain.interfaces.repository import ConnectionRepository


class PostgresConnectionRepository(ConnectionRepository):
    def __init__(self, dsn: str = settings.POSTGRES_META_DSN):
        self.engine: AsyncEngine = create_async_engine(
            dsn,
            future=True,
            echo=False,
            pool_pre_ping=True,
        )

    async def _ensure_table(self) -> None:
        async with self.engine.begin() as conn:
            await conn.execute(
                text(
                    """
                    CREATE TABLE IF NOT EXISTS enmask_connections (
                        id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        type TEXT NOT NULL,
                        host TEXT NOT NULL,
                        port INTEGER NOT NULL,
                        database TEXT NOT NULL,
                        username TEXT NOT NULL,
                        password TEXT NOT NULL,
                        additional_options TEXT
                    )
                    """
                )
            )

    async def create(self, entity: ConnectionConfig) -> ConnectionConfig:
        await self._ensure_table()
        entity_dict = entity.model_dump()
        entity_dict["id"] = entity_dict.get("id") or str(uuid.uuid4())
        entity_dict["additional_options"] = json.dumps(entity_dict.get("additional_options", {}))

        async with self.engine.begin() as conn:
            await conn.execute(
                text(
                    "INSERT INTO enmask_connections (id, name, type, host, port, database, username, password, additional_options)"
                    " VALUES (:id, :name, :type, :host, :port, :database, :username, :password, :additional_options)"
                ),
                **entity_dict,
            )

        return ConnectionConfig(**entity_dict)

    async def get_by_id(self, id: str) -> Optional[ConnectionConfig]:
        await self._ensure_table()
        async with self.engine.connect() as conn:
            result = await conn.execute(
                text("SELECT * FROM enmask_connections WHERE id = :id"),
                {"id": id},
            )
            row = result.mappings().first()
            if not row:
                return None
            record = dict(row)
            record["additional_options"] = json.loads(record.get("additional_options") or "{}")
            return ConnectionConfig(**record)

    async def get_all(self) -> List[ConnectionConfig]:
        await self._ensure_table()
        async with self.engine.connect() as conn:
            result = await conn.execute(text("SELECT * FROM enmask_connections"))
            rows = result.mappings().all()
            connections = []
            for row in rows:
                record = dict(row)
                record["additional_options"] = json.loads(record.get("additional_options") or "{}")
                connections.append(ConnectionConfig(**record))
            return connections

    async def update(self, id: str, entity: ConnectionConfig) -> Optional[ConnectionConfig]:
        await self._ensure_table()
        entity_dict = entity.model_dump()
        entity_dict["additional_options"] = json.dumps(entity_dict.get("additional_options", {}))
        async with self.engine.begin() as conn:
            await conn.execute(
                text(
                    "UPDATE enmask_connections SET name=:name, type=:type, host=:host, port=:port, database=:database, username=:username, password=:password, additional_options=:additional_options"
                    " WHERE id=:id"
                ),
                **entity_dict,
            )
        return entity

    async def delete(self, id: str) -> bool:
        await self._ensure_table()
        async with self.engine.begin() as conn:
            result = await conn.execute(text("DELETE FROM enmask_connections WHERE id = :id"), {"id": id})
            return result.rowcount == 1
