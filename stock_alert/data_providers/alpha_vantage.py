import json
from typing import Optional
import urllib.parse
import urllib.request

from ..core import Quote
from .base import DataProvider
from dev_common.core_utils import read_value_from_credential_file
from dev_common.constants import CREDENTIALS_FILE, ALPHAVANTAGE_API_KEY_KEY
from pathlib import Path


class AlphaVantageProvider(DataProvider):
    """Alpha Vantage Global Quote API.

    Credential key: ALPHAVANTAGE_API_KEY in .my_credential.env
    Endpoint: https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=SYM&apikey=KEY
    Free tier: yes (rate limited).
    """

    BASE_URL = "https://www.alphavantage.co/query"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or read_value_from_credential_file(str(Path.cwd() / CREDENTIALS_FILE), ALPHAVANTAGE_API_KEY_KEY)
        if not self.api_key:
            raise ValueError("ALPHAVANTAGE_API_KEY not set in credentials file .my_credential.env")

    def get_quote(self, symbol: str) -> Quote:
        sym = symbol.upper()
        params = {
            "function": "GLOBAL_QUOTE",
            "symbol": sym,
            "apikey": self.api_key,
        }
        url = f"{self.BASE_URL}?" + urllib.parse.urlencode(params)
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        quote = data.get("Global Quote") or data.get("GlobalQuote") or {}
        if not quote:
            raise ValueError(f"No quote data for symbol: {sym}")
        price = float(quote.get("05. price") or quote.get("price") or 0.0)
        # change percent like '0.56%'
        pct_raw = quote.get("10. change percent") or quote.get("changePercent") or "0%"
        try:
            pct_day = float(str(pct_raw).strip().rstrip("%"))
        except ValueError:
            pct_day = 0.0
        # Alpha Vantage Global Quote may include volume as "06. volume"
        try:
            volume = int(quote.get("06. volume") or quote.get("volume") or 0)
        except (TypeError, ValueError):
            volume = 0
        return Quote(symbol=sym, price=round(price, 2), pct_day=round(pct_day, 2), volume=volume)
