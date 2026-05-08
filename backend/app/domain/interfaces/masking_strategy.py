from abc import ABC, abstractmethod
from typing import Any

class MaskingStrategy(ABC):
    @abstractmethod
    def mask(self, value: Any, **options) -> Any:
        """
        Mask the given value according to the strategy implementation.
        """
        pass
