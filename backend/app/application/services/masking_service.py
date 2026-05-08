from typing import List

from app.application.schemas import RuleCreate, RuleResponse
from app.core.exceptions import ResourceNotFoundError
from app.domain.entities.masking_rule import MaskingRule
from app.domain.interfaces.repository import ConnectionRepository, RuleRepository
from app.infrastructure.repositories.memory_repository import rule_repository, connection_repository


class MaskingService:
    def __init__(self, repository: RuleRepository, connection_repository: ConnectionRepository):
        self._repository = repository
        self._connection_repository = connection_repository

    async def create_rule(self, data: RuleCreate, owner_id: str) -> RuleResponse:
        connection = await self._connection_repository.get_by_id(data.connection_id)
        if not connection or getattr(connection, "owner_id", None) != owner_id:
            raise ResourceNotFoundError("Connection", data.connection_id)

        rule = MaskingRule(**data.model_dump(), owner_id=owner_id)
        created = await self._repository.create(rule)
        return RuleResponse.model_validate(created.model_dump())

    async def get_all_rules(self, owner_id: str) -> List[RuleResponse]:
        rules = await self._repository.get_all()
        owned_rules = [r for r in rules if getattr(r, "owner_id", None) == owner_id]
        return [RuleResponse.model_validate(r.model_dump()) for r in owned_rules]

    async def get_rule(self, id: str, owner_id: str) -> RuleResponse:
        rule = await self._repository.get_by_id(id)
        if not rule or getattr(rule, "owner_id", None) != owner_id:
            raise ResourceNotFoundError("Rule", id)
        return RuleResponse.model_validate(rule.model_dump())

    async def delete_rule(self, id: str, owner_id: str) -> bool:
        rule = await self._repository.get_by_id(id)
        if not rule or getattr(rule, "owner_id", None) != owner_id:
            raise ResourceNotFoundError("Rule", id)
        success = await self._repository.delete(id)
        if not success:
            raise ResourceNotFoundError("Rule", id)
        return True


masking_service = MaskingService(rule_repository, connection_repository)
