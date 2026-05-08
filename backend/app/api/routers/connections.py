from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from app.api.deps import get_current_active_user, get_connection_service
from app.application.schemas import ConnectionCreate, ConnectionResponse, RuleCreate
from app.application.services.connection_service import ConnectionService
from app.core.exceptions import ResourceNotFoundError
from app.domain.entities.user import User
router = APIRouter(prefix="/connections", tags=["Connections"])
@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_connection(
    data: ConnectionCreate,
    current_user: User = Depends(get_current_active_user),
):
    try:
        from app.api.deps import get_connection_repository
        repo = await get_connection_repository()
        service = ConnectionService(repo)
        return await service.create_connection(data, current_user.id)
    except Exception as e:
        import traceback
        raise HTTPException(status_code=500, detail=f"ERROR: {str(e)} | TRACE: {traceback.format_exc()}")
@router.get("/")
async def list_connections(
    current_user: User = Depends(get_current_active_user),
):
    try:
        from app.api.deps import get_connection_repository
        repo = await get_connection_repository()
        service = ConnectionService(repo)
        return await service.get_all_connections(current_user.id)
    except Exception as e:
        import traceback
        raise HTTPException(status_code=500, detail=f"ERROR: {str(e)} | TRACE: {traceback.format_exc()}")
@router.get("/{conn_id}", response_model=ConnectionResponse)
async def get_connection(
    conn_id: str,
    service: ConnectionService = Depends(get_connection_service),
    current_user: User = Depends(get_current_active_user),
):
    try:
        return await service.get_connection(conn_id, current_user.id)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
@router.delete("/{conn_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_connection(
    conn_id: str,
    service: ConnectionService = Depends(get_connection_service),
    current_user: User = Depends(get_current_active_user),
):
    try:
        await service.delete_connection(conn_id, current_user.id)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
@router.get("/{conn_id}/discover", response_model=List[RuleCreate])
async def discover_connection_pii(
    conn_id: str,
    service: ConnectionService = Depends(get_connection_service),
    current_user: User = Depends(get_current_active_user),
):
    try:
        return await service.discover_pii(conn_id, current_user.id)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Discovery failed: {str(e)}")
