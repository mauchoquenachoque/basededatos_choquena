from fastapi import APIRouter, Depends
from app.api.deps import get_current_active_user, get_connection_repository, get_job_repository, get_rule_repository
from app.domain.entities.user import User
from app.domain.interfaces.repository import ConnectionRepository, JobRepository, RuleRepository

router = APIRouter(prefix="/reports", tags=["Reports"])

@router.get("/summary")
async def get_summary(
    current_user: User = Depends(get_current_active_user),
    connection_repository: ConnectionRepository = Depends(get_connection_repository),
    rule_repository: RuleRepository = Depends(get_rule_repository),
    job_repository: JobRepository = Depends(get_job_repository),
):
    connections = await connection_repository.get_all()
    rules = await rule_repository.get_all()
    jobs = await job_repository.get_all()

    if current_user.role != "admin":
        connections = [c for c in connections if getattr(c, "owner_id", None) == current_user.id]
        rules = [r for r in rules if getattr(r, "owner_id", None) == current_user.id]
        jobs = [j for j in jobs if getattr(j, "owner_id", None) == current_user.id]

    return {
        "total_connections": len(connections),
        "total_rules": len(rules),
        "total_jobs": len(jobs),
        "total_records_processed": sum(j.records_processed for j in jobs),
    }
