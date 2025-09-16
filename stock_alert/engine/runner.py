import json
import time
from typing import Callable, Dict, Iterable, Optional
from datetime import datetime

from stock_alert.common.constants import (
    CACHE_FIELD_LAST_ALERT_TRIGGER_TS,
    CACHE_FIELD_ALERTS_HISTORY,
)

from ..common.utils import LOG, seconds_from_interval
from ..core import Alert, Quote, CacheConfig
from ..data_providers import DataProvider
from ..store.cache import get_latest_cache_file, save_to_cache


def run_check(
    provider: DataProvider,
    symbols: Iterable[str],
    alerts: Dict[str, Alert],
    cache_config: CacheConfig,
    on_alert: Optional[Callable] = None,
    on_tick: Optional[Callable] = None,
) -> None:
    """Fetches quotes for all symbols and checks all alerts once."""
    now_ts = time.time()
    # Create a human-readable timestamp
    readable_timestamp = datetime.fromtimestamp(now_ts).strftime("%Y-%m-%d %H:%M:%S")

    cache_file = get_latest_cache_file(cache_config)
    if cache_file.exists():
        with open(cache_file, "r") as f:
            cache_data = json.load(f)
    else:
        cache_data = {}

    last_trigger_ts = cache_data.get(CACHE_FIELD_LAST_ALERT_TRIGGER_TS, {})
    alerts_history = cache_data.get(CACHE_FIELD_ALERTS_HISTORY, {})

    quotes: Dict[str, Quote] = {}
    for sym in sorted(symbols):
        try:
            quotes[sym] = provider.get_quote(sym)
        except Exception as e:
            LOG(f"Warning: Could not fetch quote for {sym}: {e}")

    if on_tick:
        on_tick(quotes)

    for name, alert in alerts.items():
        q = quotes.get(alert.symbol)
        if not q:
            continue

        last_ts = last_trigger_ts.get(name)
        # Get last alert record for this alert name, if any
        last_records = alerts_history.get(name) or []
        last_info = last_records[-1] if last_records else None
        should, reason = alert.should_trigger(q, now_ts, last_ts, last_info)

        if should:
            last_trigger_ts[name] = readable_timestamp
            # append alert info to history
            record = {
                "trigger_ts": readable_timestamp,
                "price_value": q.price,
                "volume": q.volume,
                "reason": reason,
            }
            # update in-memory structures
            if name not in alerts_history:
                alerts_history[name] = []
            alerts_history[name].append(record)
            # persist both timestamps and history, preserving other cache fields
            save_to_cache(
                cache_config,
                {
                    CACHE_FIELD_LAST_ALERT_TRIGGER_TS: last_trigger_ts,
                    CACHE_FIELD_ALERTS_HISTORY: alerts_history,
                },
            )
            if on_alert:
                on_alert(name, alert, q, reason)


def run_loop(
    provider: DataProvider,
    symbols: Iterable[str],
    alerts: Dict[str, Alert],
    cache_config: CacheConfig,
    interval_str: str,
    iterations: Optional[int],
    on_alert: Optional[Callable] = None,
    on_tick: Optional[Callable] = None,
):
    """The main evaluation loop."""
    interval_sec = seconds_from_interval(interval_str)

    i = 0
    while iterations is None or i < iterations:
        run_check(
            provider=provider,
            symbols=symbols,
            alerts=alerts,
            cache_config=cache_config,
            on_alert=on_alert,
            on_tick=on_tick,
        )
        i += 1
        if iterations is not None and i >= iterations:
            break

        LOG(f"Next check in {interval_sec} seconds...")
        time.sleep(max(1, interval_sec))
