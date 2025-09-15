import time
from typing import Callable, Dict, Iterable, Optional

from ..common.utils import LOG, seconds_from_interval
from ..core import Alert, Quote
from ..data_providers import DataProvider


def run_check(
    provider: DataProvider,
    symbols: Iterable[str],
    alerts: Dict[str, Alert],
    on_alert: Optional[Callable] = None,
    on_tick: Optional[Callable] = None,
) -> None:
    """Fetches quotes for all symbols and checks all alerts once."""
    now_ts = time.time()
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
        should, reason = alert.should_trigger(q, now_ts)
        if should:
            alert.last_trigger_ts = now_ts
            if on_alert:
                on_alert(name, alert, q, reason)


def run_loop(
    provider: DataProvider,
    symbols: Iterable[str],
    alerts: Dict[str, Alert],
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
            on_alert=on_alert,
            on_tick=on_tick,
        )
        i += 1
        if iterations is not None and i >= iterations:
            break

        LOG(f"Next check in {interval_sec} seconds...")
        time.sleep(max(1, interval_sec))
