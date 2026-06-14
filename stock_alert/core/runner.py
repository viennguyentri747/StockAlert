import json
import time
from typing import Any, Callable, Dict, Iterable, Optional, List
from datetime import datetime
import pdb
from stock_alert.common import *
from stock_alert.data_providers import DataProvider
from stock_alert.core.cache_utils import *


def run_check(provider: DataProvider, symbols: Iterable[str], alerts: Dict[str, Alert], cache_config: CacheConfig, callback_alert_trigger: Optional[Callable] = None, on_tick: Optional[Callable] = None, ) -> None:
    """Fetches quotes for all symbols and checks all alerts once."""
    now_ts = time.time()
    # Create a human-readable timestamp
    readable_timestamp = datetime.fromtimestamp(now_ts).strftime("%Y-%m-%d %H:%M:%S")

    cache_file = get_latest_cache_file(cache_config)
    if cache_file.exists():
        try:
            with open(cache_file, "r") as f:
                content = f.read().strip()
                cache_data = json.loads(content) if content else {}
        except Exception as e:
            LOG(f"Warning: Failed to read cache file {cache_file}: {e}. Using empty cache.")
            cache_data = {}
    else:
        cache_data = {}

    last_trigger_ts = cache_data.get(CACHE_FIELD_LAST_ALERTS_TRIGGER_TS, {})
    if not isinstance(last_trigger_ts, dict):
        last_trigger_ts = {}

    # Use the new schema only: 'old_prices'
    price_history_cache = cache_data.get(CACHE_FIELD_OLD_PRICES, {})
    if not isinstance(price_history_cache, dict):
        price_history_cache = {}

    # last_prices_update_ts = cache_data.get(CACHE_FIELD_LAST_UPDATED_TIMESTAMP)
    quotes: Dict[str, Quote] = {}
    for sym in sorted(symbols):
        try:
            quotes[sym] = provider.get_quote(sym)
        except Exception as e:
            LOG(f"Warning: Could not fetch quote for {sym}: {e}")

    if on_tick:
        on_tick(quotes)

    cache_updates: Dict[str, Any] = {}

    if quotes:
        latest_prices_payload: Dict[str, Any] = {}
        old_price_cache_interval = cache_config.old_price_cache_interval_secs
        for sym, quote in quotes.items():
            # Track the latest price per symbol
            latest_prices_payload[sym] = {
                CACHE_FIELD_SYMBOL_PRICE_TIMESTAMP: readable_timestamp,
                CACHE_FIELD_SYMBOL_PRICE: quote.price,
            }

            # Determine last old price update timestamp for this symbol (if any)
            last_old_price_update_ts = None
            existing_history_for_read = price_history_cache.get(sym, [])
            if isinstance(existing_history_for_read, list) and existing_history_for_read:
                last_entry = existing_history_for_read[-1]
                last_ts_raw = last_entry.get(CACHE_FIELD_SYMBOL_PRICE_TIMESTAMP)
                if isinstance(last_ts_raw, (int, float)):
                    last_old_price_update_ts = float(last_ts_raw)
                elif isinstance(last_ts_raw, str):
                    try:
                        last_old_price_update_ts = parse_timestamp(last_ts_raw).timestamp()
                    except ValueError:
                        last_old_price_update_ts = None

            should_update_old_prices = (last_old_price_update_ts is None or now_ts -
                                        last_old_price_update_ts >= old_price_cache_interval)
            cache_updates[CACHE_FIELD_LAST_UPDATED_TIMESTAMP] = readable_timestamp
            cache_updates[CACHE_FIELD_LATEST_PRICES] = latest_prices_payload
            if should_update_old_prices:
                existing_history = price_history_cache.setdefault(sym, [])
                if not isinstance(existing_history, list):
                    existing_history = []
                    price_history_cache[sym] = existing_history

                price_pct_threshold = cache_config.price_pct_threshold_vs_orig
                if existing_history and price_pct_threshold > 0:
                    last_entry = existing_history[-1]
                    if isinstance(last_entry, dict):
                        last_price = last_entry.get(CACHE_FIELD_SYMBOL_PRICE)
                        if isinstance(last_price, (int, float)):
                            last_price_val = float(last_price)
                            if last_price_val != 0:
                                price_pct_change = abs((quote.price - last_price_val) / last_price_val) * 100
                            else:
                                price_pct_change = INFINITY_FLOAT_VALUE

                            if price_pct_change <= price_pct_threshold:
                                # Ignore price change if it is less than the threshold, just update the last ignored timestamp
                                last_entry[CACHE_FIELD_SYMBOL_LAST_IGNORE_PRICE_TS] = readable_timestamp
                                cache_updates[CACHE_FIELD_OLD_PRICES] = price_history_cache
                                continue

                existing_history.append({
                    CACHE_FIELD_SYMBOL_PRICE_TIMESTAMP: readable_timestamp,
                    CACHE_FIELD_SYMBOL_PRICE: quote.price,
                })
                cache_updates[CACHE_FIELD_OLD_PRICES] = price_history_cache

    alerts_updated = False
    alerts_history_cache: Dict[str, List[Dict[str, Any]]] = cache_data.get(CACHE_FIELD_ALERTS_HISTORY, {})
    if not isinstance(alerts_history_cache, dict):
        alerts_history_cache = {}

    for alert_key, alert in alerts.items():
        q = quotes.get(alert.symbol)
        if not q:
            continue

        last_ts = last_trigger_ts.get(alert_key)
        # Get last alert record for this alert name, if any (for checking last trigger and other info)
        last_alert_records = alerts_history_cache.get(alert_key) or []
        # pdb.set_trace()
        # TODO: fix this because log return sth wrong here
        last_record = last_alert_records[-1] if last_alert_records else None
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
            alerts_updated = True
            if callback_alert_trigger:
                callback_alert_trigger(alert_key, alert, q, reason_trigger)

    if alerts_updated:
        cache_updates[CACHE_FIELD_LAST_ALERTS_TRIGGER_TS] = last_trigger_ts
        cache_updates[CACHE_FIELD_ALERTS_HISTORY] = alerts_history_cache

    if cache_updates:
        save_to_cache(cache_config, data=cache_updates)


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
            callback_alert_trigger=on_alert,
            on_tick=on_tick,
        )
        i += 1
        if iterations is not None and i >= iterations:
            break

        LOG(f"Next check for SYMBOLS {', '.join(symbols)} in {interval_sec} secs...")
        time.sleep(max(1, interval_sec))
