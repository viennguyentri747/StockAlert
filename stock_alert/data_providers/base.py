from abc import ABC, abstractmethod
from stock_alert.common import *

class DataProvider(ABC):
    @abstractmethod
    def get_quote(self, symbol: str) -> Quote:
        ...

