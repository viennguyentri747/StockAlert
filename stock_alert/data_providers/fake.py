import random
from typing import Optional

from ..core import Quote
from .base import DataProvider


class FakeDataProvider(DataProvider):
    def __init__(self, seed: Optional[int] = None):
        self.random = random.Random(seed)

    def get_quote(self, symbol: str) -> Quote:
        base = sum(ord(c) for c in symbol) % 200 + 20
        price = round(base + self.random.uniform(-5, 5), 2)
        pct_day = round(self.random.uniform(-5, 5), 2)
        volume = int(abs(self.random.gauss(2_000_000, 500_000)))
        return Quote(symbol=symbol.upper(), price=price, pct_day=pct_day, volume=volume)
