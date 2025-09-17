import json
from typing import Optional
import urllib.parse
import urllib.request
from pathlib import Path

from ..core import Quote
from .base import DataProvider
from ..common.utils import read_value_from_credential_file
from ..common.constants import CREDENTIALS_FILE_PATH, FINNHUB_API_KEY


class FinnhubProvider(DataProvider):
    """Finnhub quote API.
    Endpoint: https://finnhub.io/api/v1/quote?symbol=SYM&token=KEY
    Free tier: yes (rate limited).
    """

    BASE_URL = "https://finnhub.io/api/v1/quote"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or read_value_from_credential_file(CREDENTIALS_FILE_PATH, FINNHUB_API_KEY)
        if not self.api_key:
            raise ValueError("FINNHUB_API_KEY not set in credentials file .my_credential.env")

    def get_quote(self, symbol: str) -> Quote:
        sym = symbol.upper()
        params = {"symbol": sym, "token": self.api_key}
        url = f"{self.BASE_URL}?" + urllib.parse.urlencode(params)
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        price = float(data.get("c") or 0.0)
        pct_day = float(data.get("dp") or 0.0)
        volume = int(data.get("v") or 0)
        return Quote(symbol=sym, price=round(price, 2), pct_day=round(pct_day, 2), volume=volume)
