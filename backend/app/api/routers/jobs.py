import asyncio
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status, Query
from typing import List, Optional
from app.api.deps import get_current_active_user, get_job_orchestrator
from app.application.schemas import JobCreate, JobResponse, DynamicQueryResponse, JobShareRequest, AuditLogEntry
from app.application.services.job_orchestrator import JobOrchestrator
from app.core.exceptions import ResourceNotFoundError
from app.domain.entities.user import User

router = APIRouter(prefix="/jobs", tags=["Jobs"])

@router.post("/", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(
    data: JobCreate,
    orchestrator: JobOrchestrator = Depends(get_job_orchestrator),
    current_user: User = Depends(get_current_active_user),
):
    try:
        return await orchestrator.create_job(data, current_user.id)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=List[JobResponse])
async def list_jobs(
    orchestrator: JobOrchestrator = Depends(get_job_orchestrator),
    current_user: User = Depends(get_current_active_user),
):
    return await orchestrator.get_all_jobs(current_user.id)

@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: str,
    orchestrator: JobOrchestrator = Depends(get_job_orchestrator),
    current_user: User = Depends(get_current_active_user),
):
    try:
        return await orchestrator.get_job(job_id, current_user.id)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/{job_id}/run")
async def run_job(
    job_id: str,
    background_tasks: BackgroundTasks,
    orchestrator: JobOrchestrator = Depends(get_job_orchestrator),
    current_user: User = Depends(get_current_active_user),
):
    try:
        # Validate job exists
        await orchestrator.get_job(job_id, current_user.id)
        # Run in background to avoid blocking
        background_tasks.add_task(orchestrator.run_job, job_id, current_user.id)
        return {"message": "Job execution started"}
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/{job_id}/unmask")
async def unmask_job(
    job_id: str,
    background_tasks: BackgroundTasks,
    orchestrator: JobOrchestrator = Depends(get_job_orchestrator),
    current_user: User = Depends(get_current_active_user),
):
    try:
        await orchestrator.get_job(job_id, current_user.id)
        background_tasks.add_task(orchestrator.unmask_job, job_id, current_user.id)
        return {"message": "Job unmasking started"}
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/{job_id}/query", response_model=DynamicQueryResponse)
async def query_job_data(
    job_id: str,
    mask: bool = Query(None),
    orchestrator: JobOrchestrator = Depends(get_job_orchestrator),
    current_user: User = Depends(get_current_active_user),
):
    """Query job data with optional mask parameter. If mask=true, apply masking. If mask=false, show original data.
    If mask is not provided, use owner-based default: owners see unmasked, others see masked."""
    try:
        records, is_owner = await orchestrator.query_data(job_id, current_user.id, current_user.email, mask_override=mask)
        return DynamicQueryResponse(
            data=records,
            total_records=len(records),
            is_masked=mask if mask is not None else not is_owner
        )
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/{job_id}/share", status_code=status.HTTP_200_OK)
async def share_job(
    job_id: str,
    request: JobShareRequest,
    orchestrator: JobOrchestrator = Depends(get_job_orchestrator),
    current_user: User = Depends(get_current_active_user),
):
    try:
        await orchestrator.share_job(job_id, current_user.id, request.email)
        return {"message": f"Job shared with {request.email}"}
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{job_id}/audit", response_model=List[AuditLogEntry])
async def get_audit_log(
    job_id: str,
    orchestrator: JobOrchestrator = Depends(get_job_orchestrator),
    current_user: User = Depends(get_current_active_user),
):
    try:
        return await orchestrator.get_audit_log(job_id, current_user.id)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
