import json
from datetime import datetime

from stock_alert.common.constants import (
    CACHE_FIELD_OLD_PRICES,
    CACHE_FIELD_SYMBOL_LAST_IGNORE_PRICE_TS,
    CACHE_FIELD_SYMBOL_PRICE,
    CACHE_FIELD_SYMBOL_PRICE_TIMESTAMP,
)
from stock_alert.common.models import CacheConfig, Quote
from stock_alert.common.utils import LOG
from stock_alert.core.runner import run_check
from stock_alert.data_providers.base import DataProvider


class StubProvider(DataProvider):
    def __init__(self, quotes):
        self.quotes = quotes

    def get_quote(self, symbol: str) -> Quote:
        return self.quotes[symbol]


def _read_cache(cache_path):
    with cache_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def test_old_price_cache_threshold(tmp_path, monkeypatch):
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    cache_file_name = "cache.json"
    cache_file = cache_dir / cache_file_name
    LOG("Using cache file:", cache_file)
    percent_change_threshold = 1.0
    sample_config = CacheConfig(
        file_name=cache_file_name,
        directory=str(cache_dir),
        max_files=1,
        max_file_size=1024 * 1024,
        old_price_cache_interval_secs=0,
        price_pct_threshold_vs_orig=percent_change_threshold,
    )

    original_price = 200.0
    provider = StubProvider({
        "ABC": Quote(symbol="ABC", price=original_price, pct_day=0.0, volume=0),
    })

    time_values = iter([1.0, 2.0, 3.0])
    monkeypatch.setattr("stock_alert.core.runner.time.time", lambda: next(time_values))
    monkeypatch.setattr("stock_alert.core.runner.LOG", lambda *_, **__: None)
    monkeypatch.setattr("stock_alert.core.cache_utils.LOG", lambda *_, **__: None)
    # Initial run, should log the first entry
    run_check(provider=provider, symbols=["ABC"], alerts={}, cache_config=sample_config)
    cache_data = _read_cache(cache_file)

    history = cache_data[CACHE_FIELD_OLD_PRICES]["ABC"]
    assert len(history) == 1
    first_entry = history[0]
    expected_first_ts = datetime.fromtimestamp(1.0).strftime("%Y-%m-%d %H:%M:%S")
    assert first_entry[CACHE_FIELD_SYMBOL_PRICE_TIMESTAMP] == expected_first_ts
    assert first_entry[CACHE_FIELD_SYMBOL_PRICE] == original_price
    assert CACHE_FIELD_SYMBOL_LAST_IGNORE_PRICE_TS not in first_entry

    # Update symbol price but within threshold, should not log new entry
    almost_over_threshold_price = original_price + original_price*(percent_change_threshold/100.0) - 0.0001
    provider.quotes["ABC"] = Quote(symbol="ABC", price=almost_over_threshold_price, pct_day=0.0, volume=0)
    run_check(provider=provider, symbols=["ABC"], alerts={}, cache_config=sample_config)
    cache_data = _read_cache(cache_file)

    history = cache_data[CACHE_FIELD_OLD_PRICES]["ABC"]
    assert len(history) == 1
    first_entry = history[0]
    expected_second_ts = datetime.fromtimestamp(2.0).strftime("%Y-%m-%d %H:%M:%S")
    assert first_entry[CACHE_FIELD_SYMBOL_PRICE_TIMESTAMP] == expected_first_ts
    assert first_entry[CACHE_FIELD_SYMBOL_PRICE] == original_price
    assert first_entry[CACHE_FIELD_SYMBOL_LAST_IGNORE_PRICE_TS] == expected_second_ts

    # Update symbol price beyond threshold, should log new entry
    new_price = original_price + original_price*(percent_change_threshold/100.0) + 0.0001
    provider.quotes["ABC"] = Quote(symbol="ABC", price=new_price, pct_day=0.0, volume=0)
    run_check(provider=provider, symbols=["ABC"], alerts={}, cache_config=sample_config)
    cache_data = _read_cache(cache_file)

    history = cache_data[CACHE_FIELD_OLD_PRICES]["ABC"]
    assert len(history) == 2
    new_entry = history[1]
    expected_third_ts = datetime.fromtimestamp(3.0).strftime("%Y-%m-%d %H:%M:%S")
    assert new_entry[CACHE_FIELD_SYMBOL_PRICE_TIMESTAMP] == expected_third_ts
    assert new_entry[CACHE_FIELD_SYMBOL_PRICE] == new_price
    assert CACHE_FIELD_SYMBOL_LAST_IGNORE_PRICE_TS not in new_entry
