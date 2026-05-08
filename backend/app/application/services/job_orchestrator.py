from datetime import datetime
from typing import List, Optional

from app.application.schemas import JobCreate, JobResponse
from app.core.exceptions import ResourceNotFoundError
from app.domain.entities.connection import ConnectionConfig
from app.domain.entities.masking_job import MaskingJob, JobStatus
from app.domain.entities.masking_rule import MaskingRule
from app.domain.value_objects.masking_algorithm import MaskingAlgorithm
from app.domain.interfaces.repository import ConnectionRepository, JobRepository, RuleRepository, AuditLogRepository, UserRepository
from app.domain.entities.audit_log import AuditLog
from app.domain.value_objects.database_type import DatabaseType
from app.infrastructure.db.postgres_client import PostgresClient
from app.infrastructure.db.mongodb_client import MongoClient, build_mongo_uri
from app.infrastructure.db.mysql_client import MySQLClient
from app.infrastructure.masking.strategies import (
    HashingStrategy,
    NullificationStrategy,
    RedactionStrategy,
    SubstitutionStrategy,
    FPEStrategy,
    PerturbationStrategy,
)


class JobOrchestrator:
    def __init__(
        self,
        connection_repository: ConnectionRepository,
        rule_repository: RuleRepository,
        job_repository: JobRepository,
        audit_repository: AuditLogRepository = None,
        user_repository: UserRepository = None,
        vault_repository = None,
    ):
        self._connection_repository = connection_repository
        self._rule_repository = rule_repository
        self._job_repository = job_repository
        self._audit_repository = audit_repository
        self._user_repository = user_repository
        self._vault_repository = vault_repository
        self._strategies = {
            MaskingAlgorithm.SUBSTITUTION: SubstitutionStrategy(),
            MaskingAlgorithm.HASHING: HashingStrategy(),
            MaskingAlgorithm.REDACTION: RedactionStrategy(),
            MaskingAlgorithm.NULLIFICATION: NullificationStrategy(),
            MaskingAlgorithm.FPE: FPEStrategy(),
            MaskingAlgorithm.PERTURBATION: PerturbationStrategy(),
        }

    async def create_job(self, data: JobCreate, owner_id: str) -> JobResponse:
        connection = await self._connection_repository.get_by_id(data.connection_id)
        if not connection or getattr(connection, "owner_id", None) != owner_id:
            raise ResourceNotFoundError("Connection", data.connection_id)

        for rule_id in data.rule_ids:
            rule = await self._rule_repository.get_by_id(rule_id)
            if not rule or getattr(rule, "owner_id", None) != owner_id:
                raise ResourceNotFoundError("Rule", rule_id)

        job = MaskingJob(connection_id=data.connection_id, rule_ids=data.rule_ids, owner_id=owner_id)
        created = await self._job_repository.create(job)
        return JobResponse.model_validate(created.model_dump())

    async def get_all_jobs(self, owner_id: str) -> List[JobResponse]:
        jobs = await self._job_repository.get_all()
        owned_jobs = [j for j in jobs if getattr(j, "owner_id", None) == owner_id]
        return [JobResponse.model_validate(j.model_dump()) for j in owned_jobs]

    async def get_job(self, id: str, owner_id: str) -> JobResponse:
        job = await self._job_repository.get_by_id(id)
        if not job or getattr(job, "owner_id", None) != owner_id:
            raise ResourceNotFoundError("Job", id)
        return JobResponse.model_validate(job.model_dump())

    async def run_job(self, job_id: str, owner_id: str) -> None:
        job = await self._job_repository.get_by_id(job_id)
        if not job or getattr(job, "owner_id", None) != owner_id:
            raise ResourceNotFoundError("Job", job_id)

        job.status = JobStatus.RUNNING
        job.started_at = datetime.utcnow()
        await self._job_repository.update(job_id, job)

        try:
            connection = await self._connection_repository.get_by_id(job.connection_id)
            if not connection or getattr(connection, "owner_id", None) != owner_id:
                raise ResourceNotFoundError("Connection", job.connection_id)

            rules: List[MaskingRule] = []
            for rule_id in job.rule_ids:
                rule = await self._rule_repository.get_by_id(rule_id)
                if rule and getattr(rule, "owner_id", None) == owner_id:
                    rules.append(rule)

            records_processed = 0
            if connection.type == DatabaseType.POSTGRES:
                dsn = (
                    f"postgresql+asyncpg://{connection.username}:{connection.password}@{connection.host}:{connection.port}/{connection.database}"
                )
                client = PostgresClient(dsn)
                records_processed = await self._process_sql(client, rules, job_id)
            elif connection.type == DatabaseType.MYSQL:
                dsn = (
                    f"mysql+aiomysql://{connection.username}:{connection.password}@{connection.host}:{connection.port}/{connection.database}"
                )
                client = MySQLClient(dsn)
                records_processed = await self._process_sql(client, rules, job_id)
            else:
                uri = build_mongo_uri(connection.host, connection.username, connection.password, connection.port)
                client = MongoClient(uri, connection.database)
                records_processed = await self._process_mongodb(client, rules, job_id)

            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.utcnow()
            job.records_processed = records_processed
            await self._job_repository.update(job_id, job)
        except Exception as exc:
            job.status = JobStatus.FAILED
            job.error_message = str(exc)
            job.completed_at = datetime.utcnow()
            await self._job_repository.update(job_id, job)

    async def _process_sql(self, client, rules: List[MaskingRule], job_id: str) -> int:
        tables = {rule.target_table for rule in rules}
        processed = 0
        for table in tables:
            table_rules = [rule for rule in rules if rule.target_table == table]
            records = await client.fetch_all(f"SELECT * FROM {table}")
            if not records:
                continue
            pk = "id" if "id" in records[0] else list(records[0].keys())[0]
            for record in records:
                updates = self._build_updates(record, table_rules)
                if updates and pk in record:
                    if self._vault_repository:
                        original_data = {col: record[col] for col in updates.keys()}
                        await self._vault_repository.save_backup(job_id, table, str(record[pk]), original_data)
                    await client.update_record(table, pk, record[pk], updates)
                    processed += 1
        return processed

    async def _process_mongodb(self, client: MongoClient, rules: List[MaskingRule], job_id: str) -> int:
        collections = {rule.target_table for rule in rules}
        processed = 0
        for collection in collections:
            records = await client.fetch_all(collection)
            for record in records:
                updates = self._build_updates(record, [rule for rule in rules if rule.target_table == collection])
                if updates:
                    if self._vault_repository:
                        original_data = {col: record[col] for col in updates.keys()}
                        await self._vault_repository.save_backup(job_id, collection, str(record["_id"]), original_data)
                    await client.update_record(collection, record["_id"], updates)
                    processed += 1
        return processed

    async def unmask_job(self, job_id: str, owner_id: str) -> None:
        job = await self._job_repository.get_by_id(job_id)
        if not job or getattr(job, "owner_id", None) != owner_id:
            raise ResourceNotFoundError("Job", job_id)
            
        if not self._vault_repository:
            raise Exception("Vault repository not configured, cannot unmask")
            
        connection = await self._connection_repository.get_by_id(job.connection_id)
        if not connection or getattr(connection, "owner_id", None) != owner_id:
            raise ResourceNotFoundError("Connection", job.connection_id)
            
        backups = await self._vault_repository.get_backups_for_job(job_id)
        if not backups:
            raise Exception("No backups found for this job, cannot unmask")
            
        try:
            if connection.type == DatabaseType.POSTGRES:
                dsn = f"postgresql+asyncpg://{connection.username}:{connection.password}@{connection.host}:{connection.port}/{connection.database}"
                client = PostgresClient(dsn)
            elif connection.type == DatabaseType.MYSQL:
                dsn = f"mysql+aiomysql://{connection.username}:{connection.password}@{connection.host}:{connection.port}/{connection.database}"
                client = MySQLClient(dsn)
            else:
                uri = build_mongo_uri(connection.host, connection.username, connection.password, connection.port)
                client = MongoClient(uri, connection.database)

            # Restore each backup
            for backup in backups:
                table = backup["table_name"]
                pk_value = backup["record_pk"]
                updates = backup["original_data"]
                
                if connection.type in [DatabaseType.POSTGRES, DatabaseType.MYSQL]:
                    # Need to know the PK column name, usually 'id'
                    # We might need to guess or do a query, but we can assume 'id' for now or fetch schema.
                    # As a safe fallback for SQL, we assume the PK is 'id'.
                    # A robust approach would store the pk column name in vault, but for now we try 'id'
                    await client.update_record(table, "id", pk_value, updates)
                else:
                    await client.update_record(table, pk_value, updates)
                    
            await self._vault_repository.delete_backups_for_job(job_id)
            
            job.status = JobStatus.UNMASKED
            await self._job_repository.update(job_id, job)
            
        except Exception as exc:
            job.error_message = f"Unmask failed: {str(exc)}"
            await self._job_repository.update(job_id, job)
            raise exc

    async def query_data(self, job_id: str, user_id: str, user_email: str, mask_override: Optional[bool] = None) -> tuple[List[dict], bool]:
        """Query data with optional mask override.
        
        Returns (records, is_owner). If mask_override is provided, it controls masking.
        Otherwise, owners see unmasked data and shared users see masked.
        """
        job = await self._job_repository.get_by_id(job_id)
        if not job:
            raise ResourceNotFoundError("Job", job_id)

        connection = await self._connection_repository.get_by_id(job.connection_id)
        if not connection:
            raise ResourceNotFoundError("Connection", job.connection_id)

        is_owner = getattr(job, "owner_id", None) == user_id
        is_shared = user_id in job.shared_with

        if not (is_owner or is_shared):
            raise ResourceNotFoundError("Job", job_id)

        # Determine if data should be masked
        if mask_override is not None:
            show_unmasked = not mask_override
        else:
            show_unmasked = is_owner

        rules: List[MaskingRule] = []
        for rule_id in job.rule_ids:
            rule = await self._rule_repository.get_by_id(rule_id)
            if rule:
                rules.append(rule)

        records = []
        if connection.type == DatabaseType.POSTGRES:
            dsn = f"postgresql+asyncpg://{connection.username}:{connection.password}@{connection.host}:{connection.port}/{connection.database}"
            client = PostgresClient(dsn)
            records = await self._query_sql(client, rules, show_unmasked)
        elif connection.type == DatabaseType.MYSQL:
            dsn = f"mysql+aiomysql://{connection.username}:{connection.password}@{connection.host}:{connection.port}/{connection.database}"
            client = MySQLClient(dsn)
            records = await self._query_sql(client, rules, show_unmasked)
        else:
            uri = build_mongo_uri(connection.host, connection.username, connection.password, connection.port)
            client = MongoClient(uri, connection.database)
            records = await self._query_mongodb(client, rules, show_unmasked)

        if self._audit_repository:
            audit_log = AuditLog(
                job_id=job_id,
                user_id=user_id,
                user_email=user_email,
                user_role=None,
                action="query",
                is_masked=not show_unmasked,
                timestamp=datetime.utcnow()
            )
            await self._audit_repository.create(audit_log)

        return records, is_owner

    async def share_job(self, job_id: str, owner_id: str, target_email: str) -> None:
        job = await self._job_repository.get_by_id(job_id)
        if not job or getattr(job, "owner_id", None) != owner_id:
            raise ResourceNotFoundError("Job", job_id)

        if not self._user_repository:
            raise Exception("UserRepository is not configured")

        target_user = await self._user_repository.get_by_email(target_email)
        if not target_user:
            raise ResourceNotFoundError("User", target_email)

        if target_user.id not in job.shared_with:
            job.shared_with.append(target_user.id)
            await self._job_repository.update(job_id, job)

    async def get_audit_log(self, job_id: str, owner_id: str) -> List[AuditLog]:
        job = await self._job_repository.get_by_id(job_id)
        if not job:
            raise ResourceNotFoundError("Job", job_id)

        if getattr(job, "owner_id", None) != owner_id:
            raise ResourceNotFoundError("Job", job_id)

        if not self._audit_repository:
            return []

        return await self._audit_repository.get_by_job_id(job_id)


    async def _query_sql(self, client, rules: List[MaskingRule], is_admin: bool) -> List[dict]:
        tables = {rule.target_table for rule in rules}
        all_records = []
        for table in tables:
            table_rules = [rule for rule in rules if rule.target_table == table]
            records = await client.fetch_all(f"SELECT * FROM {table}")
            if not records:
                continue
            
            for record in records:
                # Convert dates/times to string to prevent JSON serialization errors
                record_dict = dict(record)
                for k, v in record_dict.items():
                    if hasattr(v, "isoformat"):
                        record_dict[k] = v.isoformat()
                        
                if not is_admin:
                    updates = self._build_updates(record_dict, table_rules)
                    record_dict.update(updates)
                all_records.append(record_dict)
        return all_records

    async def _query_mongodb(self, client: MongoClient, rules: List[MaskingRule], is_admin: bool) -> List[dict]:
        collections = {rule.target_table for rule in rules}
        all_records = []
        for collection in collections:
            records = await client.fetch_all(collection)
            for record in records:
                record_dict = dict(record)
                if "_id" in record_dict:
                    record_dict["_id"] = str(record_dict["_id"])
                    
                if not is_admin:
                    updates = self._build_updates(record_dict, [rule for rule in rules if rule.target_table == collection])
                    record_dict.update(updates)
                all_records.append(record_dict)
        return all_records

    def _build_updates(self, record: dict, rules: List[MaskingRule]) -> dict:
        updates = {}
        for rule in rules:
            if rule.target_column in record:
                strategy = self._strategies[rule.strategy]
                updates[rule.target_column] = strategy.mask(record[rule.target_column], **(rule.strategy_options or {}))
        return updates


from app.infrastructure.repositories.memory_repository import (
    connection_repository,
    job_repository,
    rule_repository,
)

job_orchestrator = JobOrchestrator(
    connection_repository=connection_repository,
    rule_repository=rule_repository,
    job_repository=job_repository,
)
