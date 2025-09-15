import argparse
import sys
from typing import List, Optional

from stock_alert.tools import t_manage_settings, t_monitor_stocks


def main(argv: Optional[List[str]] = None) -> int:
    """Main CLI entry point for the Stock Alert tool suite."""
    parser = argparse.ArgumentParser(
        description="Stock Alert tool suite. Use 'manage' for settings and 'monitor' to run.",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="tool")

    # Manage Tool
    manage_parser = subparsers.add_parser(
        "manage",
        help="Manage watchlists and alerts (e.g., 'stock-alert manage watchlist add AAPL').",
        add_help=False,  # Let the subcommand handle its own help
    )
    manage_parser.set_defaults(func=t_manage_settings.main)

    # Monitor Tool
    monitor_parser = subparsers.add_parser(
        "monitor",
        help="Monitor stocks and trigger alerts (e.g., 'stock-alert monitor --provider yahoo').",
        add_help=False,  # Let the subcommand handle its own help
    )
    monitor_parser.set_defaults(func=t_monitor_stocks.main)

    args, remainder = parser.parse_known_args(argv)

    if not hasattr(args, "func"):
        parser.print_help()
        return 1

    # Call the selected tool's main function with the remaining arguments
    return args.func(remainder)


if __name__ == "__main__":
    sys.exit(main())
