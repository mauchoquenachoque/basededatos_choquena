from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any

from app.domain.value_objects.masking_algorithm import MaskingAlgorithm


class MaskingRule(BaseModel):
    id: Optional[str] = None
    name: str
    connection_id: str
    target_table: str
    target_column: str
    strategy: MaskingAlgorithm
    strategy_options: Optional[Dict[str, Any]] = None
    owner_id: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
