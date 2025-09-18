import argparse
import sys
from typing import List, Optional
import json
from pathlib import Path
from stock_alert.common import *
from stock_alert.core import *


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
        alert = Alert(symbol=args.symbol.upper(), kind=kind, op=op, value=value, alert_cooldown_secs=args.cooldown, )
        alerts[alert.name] = alert
        save_alerts(alerts_to_dict(alerts))
        LOG(f"Created alert '{alert.name}' for {alert.symbol}: {kind.value} {op.value} {value}")
    except ValueError as e:
        LOG(f"Error: Invalid condition. {e}", file=sys.stderr)
        sys.exit(1)

def parse_condition(cond: str) -> Tuple[AlertKind, Operation, float]:
    _KINDS_PATTERN = "|".join(k.value for k in AlertKind)
    ALERT_RE = re.compile(rf"^({_KINDS_PATTERN})\s*(>=|<=)\s*(-?\d+(?:\.\d+)?)$", re.IGNORECASE, )
    m = ALERT_RE.match(cond.strip())
    if not m:
        raise ValueError(
            f"Condition must be like: '{AlertKind.PRICE_VALUE.value} >= 200', '{AlertKind.PCT_DAY.value} <= -3', "
            f"'{AlertKind.VOLUME.value} >= 1000000', '{AlertKind.PRICE_PERCENT_OFFSET_SINCE_LAST_ALERT.value} >= 5', "
        )
    kind_s, op_s, value = m.group(1).lower(), m.group(2), float(m.group(3))
    kind = AlertKind(kind_s)
    op = Operation(op_s)
    return kind, op, value

def cmd_alerts_list(_args: argparse.Namespace):
    """Lists all configured alerts."""
    alerts = alerts_from_dict(load_alerts())
    if not alerts:
        LOG("No alerts defined.")
        return

    # Load cache data to get last trigger timestamps
    config = load_config()
    cache_config = CacheConfig.from_dict(config.get(CACHE_CORE_CONFIG_KEY, {}))
    cache_file = Path(cache_config.directory) / cache_config.file_name

    cache_data = {}
    if cache_file.exists():
        try:
            with open(cache_file, "r") as f:
                cache_data = json.load(f)
        except Exception:
            pass

    last_trigger_ts = cache_data.get("last_alert_trigger_ts", {})

    LOG("Alerts:")
    for name, a in sorted(alerts.items()):
        last = last_trigger_ts.get(name, "never")
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
        "--when", required=True, help="Condition string, e.g., 'price_value >= 200', 'pct_day <= -3', 'volume >= 1000000', 'last_alert_price_offset_percent >= 5', 'last_alert_price_value >= 150'", )
    p_a_create.add_argument("--name", required=True, help="A unique name for the alert")
    p_a_create.add_argument("--cooldown", type=int, default=DEFAULT_COOLDOWN_SEC,
                            help=f"Trigger cooldown in seconds (default: {DEFAULT_COOLDOWN_SEC})", )
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
