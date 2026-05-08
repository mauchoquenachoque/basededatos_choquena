from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from app.api.deps import get_current_active_user, get_masking_service
from app.application.schemas import RuleCreate, RuleResponse
from app.application.services.masking_service import MaskingService
from app.core.exceptions import ResourceNotFoundError
from app.domain.entities.user import User

router = APIRouter(prefix="/rules", tags=["Rules"])

@router.post("/", response_model=RuleResponse, status_code=status.HTTP_201_CREATED)
async def create_rule(
    data: RuleCreate,
    service: MaskingService = Depends(get_masking_service),
    current_user: User = Depends(get_current_active_user),
):
    return await service.create_rule(data, current_user.id)

@router.get("/", response_model=List[RuleResponse])
async def list_rules(
    service: MaskingService = Depends(get_masking_service),
    current_user: User = Depends(get_current_active_user),
):
    return await service.get_all_rules(current_user.id)

@router.get("/{rule_id}", response_model=RuleResponse)
async def get_rule(
    rule_id: str,
    service: MaskingService = Depends(get_masking_service),
    current_user: User = Depends(get_current_active_user),
):
    try:
        return await service.get_rule(rule_id, current_user.id)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rule(
    rule_id: str,
    service: MaskingService = Depends(get_masking_service),
    current_user: User = Depends(get_current_active_user),
):
    try:
        await service.delete_rule(rule_id, current_user.id)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
