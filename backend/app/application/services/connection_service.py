from typing import List

from app.application.schemas import ConnectionCreate, ConnectionResponse
from app.core.exceptions import ResourceNotFoundError
from app.domain.entities.connection import ConnectionConfig
from app.domain.interfaces.repository import ConnectionRepository
from app.infrastructure.repositories.memory_repository import connection_repository
from app.domain.value_objects.database_type import DatabaseType
from app.infrastructure.db.postgres_client import PostgresClient
from app.infrastructure.db.mongodb_client import MongoClient
from app.infrastructure.db.mysql_client import MySQLClient
from app.domain.services.pii_detector import pii_detector
from app.application.schemas import RuleCreate


class ConnectionService:
    def __init__(self, repository: ConnectionRepository):
        self._repository = repository

    async def create_connection(self, data: ConnectionCreate, owner_id: str) -> ConnectionResponse:
        connection = ConnectionConfig(**data.model_dump(), owner_id=owner_id)
        created = await self._repository.create(connection)
        return ConnectionResponse.model_validate(created.model_dump())

    async def get_all_connections(self, owner_id: str) -> List[ConnectionResponse]:
        connections = await self._repository.get_all()
        owned_connections = [c for c in connections if getattr(c, "owner_id", None) == owner_id]
        return [ConnectionResponse.model_validate(c.model_dump()) for c in owned_connections]

    async def get_connection(self, id: str, owner_id: str) -> ConnectionResponse:
        connection = await self._repository.get_by_id(id)
        if not connection or getattr(connection, "owner_id", None) != owner_id:
            raise ResourceNotFoundError("Connection", id)
        return ConnectionResponse.model_validate(connection.model_dump())

    async def delete_connection(self, id: str, owner_id: str) -> bool:
        connection = await self._repository.get_by_id(id)
        if not connection or getattr(connection, "owner_id", None) != owner_id:
            raise ResourceNotFoundError("Connection", id)
        success = await self._repository.delete(id)
        if not success:
            raise ResourceNotFoundError("Connection", id)
        return True

    async def discover_pii(self, id: str, owner_id: str) -> List[RuleCreate]:
        connection = await self._repository.get_by_id(id)
        if not connection or getattr(connection, "owner_id", None) != owner_id:
            raise ResourceNotFoundError("Connection", id)

        if connection.type == DatabaseType.POSTGRES:
            dsn = f"postgresql+asyncpg://{connection.username}:{connection.password}@{connection.host}:{connection.port}/{connection.database}"
            client = PostgresClient(dsn)
            schema = await client.get_schema()
        elif connection.type == DatabaseType.MYSQL:
            dsn = f"mysql+aiomysql://{connection.username}:{connection.password}@{connection.host}:{connection.port}/{connection.database}"
            client = MySQLClient(dsn)
            schema = await client.get_schema()
        else:
            import urllib.parse
            enc_user = urllib.parse.quote_plus(connection.username)
            enc_pass = urllib.parse.quote_plus(connection.password)
            uri = f"mongodb+srv://{enc_user}:{enc_pass}@{connection.host}/"
            client = MongoClient(uri, connection.database)
            schema = await client.get_schema()

        suggestions = pii_detector.discover(schema)
        rules = []
        for s in suggestions:
            rules.append(RuleCreate(
                name=f"Auto-{s.target_table}-{s.target_column}",
                connection_id=id,
                target_table=s.target_table,
                target_column=s.target_column,
                strategy=s.strategy,
                strategy_options=s.strategy_options
            ))
        return rules


connection_service = ConnectionService(connection_repository)
