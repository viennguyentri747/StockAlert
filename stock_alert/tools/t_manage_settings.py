import argparse
import sys
import time
from typing import List, Optional

from stock_alert.common.constants import DEFAULT_COOLDOWN_SEC
from stock_alert.common.utils import LOG
from stock_alert.core import Alert, parse_condition
from stock_alert.store import (
    alerts_from_dict,
    alerts_to_dict,
    load_alerts,
    load_watchlist,
    save_alerts,
    save_watchlist,
)


def cmd_watchlist_add(args: argparse.Namespace):
    """Adds symbols to the watchlist."""
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
    """Lists all symbols in the watchlist."""
    symbols = load_watchlist()
    if not symbols:
        LOG("Watchlist is empty.")
    else:
        LOG("Watchlist:")
        for s in sorted(symbols):
            LOG(f"- {s}")


def cmd_alert_create(args: argparse.Namespace):
    """Creates a new alert."""
    alerts = alerts_from_dict(load_alerts())
    if args.name in alerts:
        LOG(f"Error: Alert with name '{args.name}' already exists.", file=sys.stderr)
        sys.exit(1)

    try:
        kind, op, value = parse_condition(args.when)
        alert = Alert(
            name=args.name,
            symbol=args.symbol.upper(),
            kind=kind,
            op=op,
            value=value,
            alert_cooldown_secs=args.cooldown,
        )
        alerts[alert.name] = alert
        save_alerts(alerts_to_dict(alerts))
        LOG(
            f"Created alert '{alert.name}' for {alert.symbol}: {kind.value} {op.value} {value}"
        )
    except ValueError as e:
        LOG(f"Error: Invalid condition. {e}", file=sys.stderr)
        sys.exit(1)


def cmd_alerts_list(_args: argparse.Namespace):
    """Lists all configured alerts."""
    alerts = alerts_from_dict(load_alerts())
    if not alerts:
        LOG("No alerts defined.")
        return
    LOG("Alerts:")
    for name, a in sorted(alerts.items()):
        last = (
            time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(a.last_trigger_ts))
            if a.last_trigger_ts
            else "never"
        )
        LOG(f"- {name}: {a.symbol} | {a.kind.value} {a.op.value} {a.value} | cooldown {a.alert_cooldown_secs}s | last {last}")


def main(argv: Optional[List[str]] = None) -> int:
    """Main function for the settings management tool."""
    parser = argparse.ArgumentParser(
        prog="stock-alert manage", description="Tool to manage watchlists and alerts."
    )
    sub = parser.add_subparsers(dest="cmd")

    # Watchlist commands
    p_w = sub.add_parser("watchlist", help="Manage the stock watchlist")
    sub_w = p_w.add_subparsers(dest="subcmd_watchlist", required=True)
    p_w_add = sub_w.add_parser("add", help="Add symbols to watchlist")
    p_w_add.add_argument("symbols", nargs="+", help="One or more stock symbols (e.g., AAPL TSLA)")
    p_w_add.set_defaults(func=cmd_watchlist_add)
    p_w_list = sub_w.add_parser("list", help="List all symbols in the watchlist")
    p_w_list.set_defaults(func=cmd_watchlist_list)

    # Alert commands
    p_a = sub.add_parser("alert", help="Manage individual alerts")
    sub_a = p_a.add_subparsers(dest="subcmd_alert", required=True)
    p_a_create = sub_a.add_parser("create", help="Create a new alert")
    p_a_create.add_argument("--symbol", required=True, help="Stock symbol for the alert")
    p_a_create.add_argument(
        "--when",
        required=True,
        help="Condition string, e.g., 'price >= 200', 'pct_day <= -3'",
    )
    p_a_create.add_argument("--name", required=True, help="A unique name for the alert")
    p_a_create.add_argument(
        "--cooldown",
        type=int,
        default=DEFAULT_COOLDOWN_SEC,
        help=f"Trigger cooldown in seconds (default: {DEFAULT_COOLDOWN_SEC})",
    )
    p_a_create.set_defaults(func=cmd_alert_create)

    # Top-level 'alerts' to list all
    p_as_list = sub.add_parser("alerts", help="List all configured alerts")
    p_as_list.set_defaults(func=cmd_alerts_list)

    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        return 1

    try:
        args.func(args)
        return 0
    except Exception as e:
        LOG(f"An error occurred: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
