import signal
import time
from typing import Dict, Iterable, Optional

from ..core import Alert, Quote
from dev_common.core_utils import seconds_from_interval, LOG


def run_loop(
    provider,
    symbols: Iterable[str],
    alerts: Dict[str, Alert],
    interval: str = "30s",
    iterations: Optional[int] = None,
    on_alert=None,
    on_tick=None,
) -> None:
    interval_sec = seconds_from_interval(interval)
    stop = False

    i = 0
    while not stop and (iterations is None or i < iterations):
        i += 1
        now_ts = time.time()

        quotes: Dict[str, Quote] = {}
        for sym in symbols:
            quotes[sym] = provider.get_quote(sym)

        triggered = []
        for name, alert in alerts.items():
            q = quotes.get(alert.symbol)
            if not q:
                continue
            should, reason = alert.should_trigger(q, now_ts)
            if should:
                alert.last_trigger_ts = now_ts
                triggered.append((name, alert, q, reason))

        if on_tick:
            on_tick(quotes)

        for name, alert, q, reason in triggered:
            if on_alert:
                on_alert(name, alert, q, reason)

        if stop or (iterations is not None and i >= iterations):
            break
        LOG(f"Next tick in {interval_sec} seconds...")
        time.sleep(max(1, interval_sec))
