import argparse
import sys
import traceback
from typing import List, Optional
from stock_alert.common import *
from stock_alert.data_providers import *
from stock_alert.core import *


def _get_provider(name: str) -> DataProvider:
    """Initializes and returns the specified data provider."""
    name = (name or "fake").lower()
    if name == "fake":
        return FakeDataProvider()
    if name in ("yahoo", "yfinance", "yahoo_finance"):
        return YahooFinanceProvider()
    if name in ("alpha", "alphavantage", "alpha_vantage"):
        return AlphaVantageProvider()
    if name in ("finnhub",):
        return FinnhubProvider()
    raise SystemExit(f"Error: Unknown provider '{name}'")


def main(argv: Optional[List[str]] = None) -> int:
    """Main function for the stock monitoring tool."""
    parser = argparse.ArgumentParser(prog="stock-alert monitor",
                                     description="Run the stock monitoring and alert engine.")
    parser.add_argument("--interval", default=DEFAULT_MONITOR_INTERVAL,
                        help=f"Polling interval, e.g., '30s', '1m' (default: {DEFAULT_MONITOR_INTERVAL})", )
    parser.add_argument("--iterations", type=int, default=None,
                        help="Stop after N iterations (default: runs forever)", )
    parser.add_argument("--verbose", action="store_true", help="Print quotes on every check")
    parser.add_argument("--provider", default="fake",
                        choices=["fake", "yahoo", "alphavantage", "finnhub"], help="Data provider to use (default: fake)", )
    args = parser.parse_args(argv)

    try:
        config = load_config()

        cache_config = CacheConfig.from_dict(config.get("cache", {}))
        cache_dir = Path(cache_config.directory)
        cache_dir.mkdir(parents=True, exist_ok=True)

        provider = _get_provider(args.provider)
        alerts = alerts_from_dict(load_alerts())
        watchlist_symbols = set(load_watchlist())
        alert_symbols = {a.symbol for a in alerts.values()}
        symbols = sorted(alert_symbols | watchlist_symbols)

        if not symbols:
            LOG("Nothing to monitor. Add symbols via 'stock-alert manage watchlist add'.")
            return 0

        LOG(f"Starting monitor for {len(symbols)} symbol(s) using '{args.provider}' provider... Symbols: {', '.join(symbols)}")
        LOG(f"Interval: {args.interval}, Iterations: {args.iterations or '∞'}")

        def on_tick(quotes):
            if args.verbose:
                for sym, q in quotes.items():
                    LOG(f"{sym:<6}: price=${q.price:<8.2f} | % day={q.pct_day:<6.2f} | vol={q.volume}")

        def on_alert(alert_key, alert: Alert, q, reason):
            LOG(f"{ALERT_LOG_TAG} {alert_key}. Current price=${q.price}, % day={q.pct_day}, vol={q.volume}")
            show_noti(title=alert.name, message=f"{reason}")

        # Run the monitoring loop
        run_loop(provider=provider, symbols=symbols, alerts=alerts, cache_config=cache_config,
                 interval_str=args.interval, iterations=args.iterations, on_alert=on_alert, on_tick=on_tick, )
        LOG("Monitoring finished.")
        return 0
    except KeyboardInterrupt:
        LOG("\nMonitoring stopped by user.")
        return 130
    except Exception as e:
        LOG(f"An error occurred: {e}\n{traceback.format_exc()}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
