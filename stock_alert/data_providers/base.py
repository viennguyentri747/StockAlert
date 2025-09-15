from abc import ABC, abstractmethod
from typing import Protocol

from ..core import Quote


class DataProvider(ABC):
    @abstractmethod
    def get_quote(self, symbol: str) -> Quote:
        ...

