from enum import Enum
from pathlib import Path

# FORMATS
LINE_SEPARATOR = f"\n{'=' * 60}\n"
LINE_SEPARATOR_NO_ENDLINE = f"{'=' * 60}"


# Data filenames
WATCHLIST_FILE = "watchlist.json"
ALERTS_FILE = "alerts.json"
CONFIG_FILE = "config.json"

# Defaults
DEFAULT_INTERVAL = "5s"
DEFAULT_COOLDOWN_SEC = 300

REPO_PATH = Path.home() / "stock_alert/"
DEFAULT_APP_DIR_PATH = f"{REPO_PATH}/.stockalert"
CREDENTIALS_FILE_PATH = f"{REPO_PATH}/.my_credentials.env"

# Alert settings


class AlertKind(str, Enum):
    PRICE = "price"
    PCT_DAY = "pct_day"
    VOLUME = "volume"


class Operation(str, Enum):
    GE = ">="
    LE = "<="


# JSON field keys (avoid magic strings)
ALERT_FIELD_NAME = "name"
ALERT_FIELD_SYMBOL = "symbol"
ALERT_FIELD_KIND = "kind"
ALERT_FIELD_VALUE = "value"
ALERT_FIELD_OP = "op"
ALERT_FIELD_ALERT_COOLDOWN = "alert_cooldown_secs"
ALERT_FIELD_LAST_TRIGGER_TS = "last_trigger_ts"

# Credential key names
ALPHAVANTAGE_API_KEY = "ALPHAVANTAGE_API_TOKEN"
FINNHUB_API_KEY = "FINNHUB_API_TOKEN"
