import pytest

from app.infrastructure.repositories.memory_repository import (
    connection_repository,
    job_repository,
    rule_repository,
)


@pytest.fixture(autouse=True)
def clear_repositories():
    connection_repository._data.clear()
    rule_repository._data.clear()
    job_repository._data.clear()
