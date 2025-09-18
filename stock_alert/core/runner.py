import json
import time
from typing import Callable, Dict, Iterable, Optional
from datetime import datetime
import pdb
from stock_alert.common import *
from stock_alert.data_providers import DataProvider
from stock_alert.core.cache_utils import *


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

    last_trigger_ts = cache_data.get(CACHE_FIELD_LAST_ALERTS_TRIGGER_TS, {})
    alerts_history_cache: Dict[str, List[Dict]] = cache_data.get(CACHE_FIELD_ALERTS_HISTORY, {})

    quotes: Dict[str, Quote] = {}
    for sym in sorted(symbols):
        try:
            quotes[sym] = provider.get_quote(sym)
        except Exception as e:
            LOG(f"Warning: Could not fetch quote for {sym}: {e}")

    if on_tick:
        on_tick(quotes)

    for alert_key, alert in alerts.items():
        q = quotes.get(alert.symbol)
        if not q:
            continue

        last_ts = last_trigger_ts.get(alert_key)
        # Get last alert record for this alert name, if any (for checking last trigger and other info)
        last_records = alerts_history_cache.get(alert_key) or []
        # pdb.set_trace()
        last_record = last_records[-1] if last_records else None
        should_trigger, reason_trigger = alert.should_trigger(q, now_ts, last_ts, last_record)
        LOG(f"Checking alert {alert_key} for {alert.symbol}: {q.price} | last trigger: {last_ts} | last record: {last_record}.  Result: Should trigger: {should_trigger}, Reason: {reason_trigger}")

        if should_trigger:
            last_trigger_ts[alert_key] = readable_timestamp
            # append alert info to history
            alert_single_record = {
                ALERT_RECORD_FIELD_TRIGGER_TS: readable_timestamp,
                ALERT_RECORD_FIELD_NAME: alert.name,
                CACHE_FIELD_ALERT_LAST_PRICE: q.price,
            }
            # update in-memory structures
            if alert_key not in alerts_history_cache:
                alerts_history_cache[alert_key] = []
            alerts_history_cache[alert_key].append(alert_single_record)
            # persist both timestamps and history, preserving other cache fields
            save_to_cache(
                cache_config,
                data={
                    CACHE_FIELD_LAST_ALERTS_TRIGGER_TS: last_trigger_ts,
                    CACHE_FIELD_ALERTS_HISTORY: alerts_history_cache,
                },
            )
            if on_alert:
                on_alert(alert_key, alert, q, reason_trigger)


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

        LOG(f"Next check for SYMBOLS {', '.join(symbols)} in {interval_sec} secs...")
        time.sleep(max(1, interval_sec))
