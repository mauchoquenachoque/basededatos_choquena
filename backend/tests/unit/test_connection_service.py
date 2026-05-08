import pytest

from app.application.schemas import ConnectionCreate
from app.application.services.connection_service import ConnectionService
from app.infrastructure.repositories.memory_repository import MemoryRepository
from app.domain.entities.connection import ConnectionConfig


class DummyConnectionRepository(MemoryRepository[ConnectionConfig]):
    pass


@pytest.mark.asyncio
async def test_create_and_get_connection():
    repo = DummyConnectionRepository()
    service = ConnectionService(repo)
    payload = ConnectionCreate(
        name="TestDB",
        type="postgres",
        host="localhost",
        port=5432,
        database="testdb",
        username="postgres",
        password="secret",
    )

    created = await service.create_connection(payload, owner_id="user1")
    assert created.id is not None
    assert created.name == "TestDB"

    fetched = await service.get_connection(created.id, owner_id="user1")
    assert fetched.id == created.id
    assert fetched.name == "TestDB"
