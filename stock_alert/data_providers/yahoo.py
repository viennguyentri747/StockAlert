import json
import urllib.parse
import urllib.request

from ..core import Quote
from .base import DataProvider


class YahooFinanceProvider(DataProvider):
    """Fetch quotes from Yahoo Finance public quote API (no key required).

    Uses endpoint:
    https://query1.finance.yahoo.com/v7/finance/quote?symbols=SYMBOL
    """

    BASE_URL = "https://query1.finance.yahoo.com/v7/finance/quote"

    def get_quote(self, symbol: str) -> Quote:
        sym = symbol.upper()
        url = f"{self.BASE_URL}?" + urllib.parse.urlencode({"symbols": sym})
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        try:
            result = data["quoteResponse"]["result"][0]
        except (KeyError, IndexError):
            raise ValueError(f"No quote data for symbol: {sym}")
        price = float(result.get("regularMarketPrice") or result.get("postMarketPrice") or 0.0)
        pct_day = float(result.get("regularMarketChangePercent") or 0.0)
        volume = int(result.get("regularMarketVolume") or 0)
        return Quote(symbol=sym, price=round(price, 2), pct_day=round(pct_day, 2), volume=volume)
