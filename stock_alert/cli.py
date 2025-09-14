import argparse
import sys
import time
from typing import Dict, List, Optional
from dev_common.constants import DEFAULT_INTERVAL, DEFAULT_COOLDOWN_SEC
from dev_common.core_utils import *

from .core import Alert, parse_condition
from .data_providers import FakeDataProvider
from .data_providers import YahooFinanceProvider, AlphaVantageProvider, FinnhubProvider
from .engine import run_loop
from .store import (
    load_watchlist,
    save_watchlist,
    load_alerts,
    save_alerts,
    alerts_from_dict,
    alerts_to_dict,
)

def cmd_watchlist_add(args: argparse.Namespace):
    symbols = load_watchlist()
    before = set(symbols)
    symbols.extend([s.upper() for s in args.symbols])
    save_watchlist(symbols)
    added = sorted(set(s.upper() for s in args.symbols) - before)
    if added:
        LOG(f"Added to watchlist: {', '.join(added)}")
    else:
        LOG("No new symbols added.")


def cmd_watchlist_list(_args: argparse.Namespace):
    symbols = load_watchlist()
    if not symbols:
        LOG("Watchlist is empty.")
    else:
        LOG("Watchlist:")
        for s in sorted(symbols):
            LOG(f"- {s}")


def cmd_alert_create(args: argparse.Namespace):
    alerts_raw = load_alerts()
    alerts = alerts_from_dict(alerts_raw)
    if args.name in alerts:
        LOG(f"Alert with name '{args.name}' already exists.", file=sys.stderr)
        sys.exit(1)

    kind, op, value = parse_condition(args.when)
    alert = Alert(
        name=args.name,
        symbol=args.symbol.upper(),
        kind=kind,
        op=op,
        value=value,
        cooldown_sec=args.cooldown,
    )
    alerts[alert.name] = alert
    save_alerts(alerts_to_dict(alerts))
    LOG(
        f"Created alert '{alert.name}' for {alert.symbol}: {kind.value} {op.value} {value}"
    )


def cmd_alerts_list(_args: argparse.Namespace):
    alerts_raw = load_alerts()
    if not alerts_raw:
        LOG("No alerts defined.")
        return
    alerts = alerts_from_dict(alerts_raw)
    LOG("Alerts:")
    for name, a in sorted(alerts.items()):
        last = (
            time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(a.last_trigger_ts))
            if a.last_trigger_ts
            else "never"
        )
        LOG(
            f"- {name}: {a.symbol} | {a.kind.value} {a.op.value} {a.value} | cooldown {a.cooldown_sec}s | last {last}"
        )


def _get_provider(name: str):
    name = (name or "fake").lower()
    if name == "fake":
        return FakeDataProvider()
    if name in ("yahoo", "yfinance", "yahoo_finance"):
        return YahooFinanceProvider()
    if name in ("alpha", "alphavantage", "alpha_vantage"):
        return AlphaVantageProvider()
    if name in ("finnhub",):
        return FinnhubProvider()
    raise SystemExit(f"Unknown provider: {name}")


def cmd_run(args: argparse.Namespace):
    provider = _get_provider(args.provider)
    alerts = alerts_from_dict(load_alerts())
    symbols = sorted({a.symbol for a in alerts.values()} | set(load_watchlist()))
    if not symbols:
        LOG("Nothing to run. Add symbols to watchlist or create alerts.")
        return

    LOG(
        f"Running with {len(symbols)} symbol(s), interval={args.interval}, iterations={args.iterations or '∞'}"
    )

    def on_tick(quotes):
        if args.verbose:
            for sym, q in quotes.items():
                LOG(f"{sym}: price={q.price} pct_day={q.pct_day}% volume={q.volume}")

    def on_alert(name, alert, q, reason):
        LOG(
            f"[ALERT] {name} ({alert.symbol}) -> {reason}. Price={q.price}, pct_day={q.pct_day}%, volume={q.volume}"
        )
        save_alerts(alerts_to_dict(alerts))

    run_loop(
        provider=provider,
        symbols=symbols,
        alerts=alerts,
        interval=args.interval,
        iterations=args.iterations,
        on_alert=on_alert,
        on_tick=on_tick,
    )
    LOG("Run finished.")


def cmd_config_set(args: argparse.Namespace):
    ensure_app_dir()
    cfg = load_json(CONFIG_FILE, {})
    # simple dotless flat set for MVP
    cfg[args.key] = args.value
    save_json(CONFIG_FILE, cfg)
    LOG(f"Set config {args.key}={args.value}")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="stock_alert", description="Stock/ETF/Crypto alert CLI (MVP)")
    sub = p.add_subparsers(dest="cmd")

    # watchlist
    p_w = sub.add_parser("watchlist", help="Manage watchlists")
    sub_w = p_w.add_subparsers(dest="subcmd")
    p_w_add = sub_w.add_parser("add", help="Add symbols to watchlist")
    p_w_add.add_argument("symbols", nargs="+", help="Symbols, e.g. AAPL TSLA")
    p_w_add.set_defaults(func=cmd_watchlist_add)

    p_w_list = sub_w.add_parser("list", help="List watchlist symbols")
    p_w_list.set_defaults(func=cmd_watchlist_list)

    # alerts
    p_a = sub.add_parser("alert", help="Create or manage alerts")
    sub_a = p_a.add_subparsers(dest="subcmd")
    p_a_create = sub_a.add_parser("create", help="Create alert")
    p_a_create.add_argument("--symbol", required=True)
    p_a_create.add_argument(
        "--when",
        required=True,
        help="e.g. 'price >= 200', 'pct_day <= -3', 'volume >= 1000000'",
    )
    p_a_create.add_argument("--name", required=True)
    p_a_create.add_argument(
        "--cooldown",
        type=int,
        default=DEFAULT_COOLDOWN_SEC,
        help=f"Cooldown seconds (default {DEFAULT_COOLDOWN_SEC})",
    )
    p_a_create.set_defaults(func=cmd_alert_create)

    p_as_list = sub.add_parser("alerts", help="List alerts")
    p_as_list.set_defaults(func=cmd_alerts_list)

    # run
    p_run: argparse.ArgumentParser = sub.add_parser("run", help="Run evaluation loop")
    p_run.add_argument(
        "--interval",
        default=DEFAULT_INTERVAL,
        help="Polling interval, e.g. 30s, 1m",
    )
    p_run.add_argument("--iterations", type=int, default=None, help="Stop after N iterations (default infinite)")
    p_run.add_argument("--verbose", action="store_true", help="Print quotes each tick")
    p_run.add_argument(
        "--provider",
        default="fake",
        help="Data provider: fake|yahoo|alphavantage|finnhub (default fake)",
    )
    p_run.set_defaults(func=cmd_run)

    # config (placeholder)
    p_cfg = sub.add_parser("config", help="Set config values (placeholder)")
    sub_cfg = p_cfg.add_subparsers(dest="subcmd")
    p_cfg_set = sub_cfg.add_parser("set", help="Set a config key (no-op)")
    p_cfg_set.add_argument("key")
    p_cfg_set.add_argument("value")
    p_cfg_set.set_defaults(func=cmd_config_set)

    return p


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        return 1
    try:
        args.func(args)
        return 0
    except KeyboardInterrupt:
        LOG("Interrupted.")
        return 130
    except Exception as e:
        LOG(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
