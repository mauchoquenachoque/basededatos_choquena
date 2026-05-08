from typing import List, Dict, Optional, Any
import re
from pydantic import BaseModel
from app.domain.value_objects.masking_algorithm import MaskingAlgorithm

class SuggestedRule(BaseModel):
    target_table: str
    target_column: str
    strategy: MaskingAlgorithm
    strategy_options: Optional[Dict[str, Any]] = None

class PIIDetector:
    def __init__(self):
        # Dictionary mapping regex patterns to their suggested masking algorithm and options
        self.heuristics = [
            (re.compile(r".*email.*|.*correo.*", re.IGNORECASE), MaskingAlgorithm.SUBSTITUTION, {"provider": "email"}),
            (re.compile(r".*password.*|.*clave.*|.*pwd.*", re.IGNORECASE), MaskingAlgorithm.HASHING, {}),
            (re.compile(r".*phone.*|.*telefono.*|.*celular.*", re.IGNORECASE), MaskingAlgorithm.SUBSTITUTION, {"provider": "phone_number"}),
            (re.compile(r".*card.*|.*tarjeta.*|.*credit.*", re.IGNORECASE), MaskingAlgorithm.REDACTION, {"mask_char": "*"}),
            (re.compile(r".*ssn.*|.*social.*security.*|.*dni.*", re.IGNORECASE), MaskingAlgorithm.REDACTION, {"mask_char": "X"}),
            (re.compile(r".*address.*|.*direccion.*", re.IGNORECASE), MaskingAlgorithm.SUBSTITUTION, {"provider": "address"}),
            (re.compile(r".*name.*|.*nombre.*", re.IGNORECASE), MaskingAlgorithm.SUBSTITUTION, {"provider": "name"}),
            (re.compile(r".*birth.*|.*nacimiento.*|.*dob.*", re.IGNORECASE), MaskingAlgorithm.SUBSTITUTION, {"provider": "date_of_birth"}),
        ]

    def discover(self, schema: Dict[str, List[str]]) -> List[SuggestedRule]:
        suggestions = []
        for table, columns in schema.items():
            for column in columns:
                suggestion = self._analyze_column(table, column)
                if suggestion:
                    suggestions.append(suggestion)
        return suggestions

    def _analyze_column(self, table: str, column: str) -> Optional[SuggestedRule]:
        for pattern, strategy, options in self.heuristics:
            if pattern.match(column):
                return SuggestedRule(
                    target_table=table,
                    target_column=column,
                    strategy=strategy,
                    strategy_options=options
                )
        return None

pii_detector = PIIDetector()
