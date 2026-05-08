from abc import ABC, abstractmethod
from typing import List, Dict, Any

class VaultRepository(ABC):
    @abstractmethod
    async def save_backup(self, job_id: str, table_name: str, record_pk: str, original_data: Dict[str, Any]) -> None:
        """Saves the original record state before masking."""
        pass

    @abstractmethod
    async def get_backups_for_job(self, job_id: str) -> List[Dict[str, Any]]:
        """Returns all backed up records for a given job. Format depends on implementation."""
        pass

    @abstractmethod
    async def delete_backups_for_job(self, job_id: str) -> None:
        """Deletes all backups associated with a job, usually after unmasking."""
        pass
