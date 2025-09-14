from enum import Enum

# FORMATS
LINE_SEPARATOR = f"\n{'=' * 60}\n"
LINE_SEPARATOR_NO_ENDLINE = f"{'=' * 60}"

APP_DIR_ENV = "STOCKALERT_HOME"
DEFAULT_APP_DIR_NAME = ".stockalert"

# Data filenames
WATCHLIST_FILE = "watchlist.json"
ALERTS_FILE = "alerts.json"
CONFIG_FILE = "config.json"

# Defaults
DEFAULT_INTERVAL = "5s"
DEFAULT_COOLDOWN_SEC = 300
 
# Credentials file (relative to current working directory)
CREDENTIALS_FILE = ".my_credential.env"

# Alert settings
class AlertKind(str, Enum):
    PRICE = "price"
    PCT_DAY = "pct_day"
    VOLUME = "volume"

class Operation(str, Enum):
    GE = ">="
    LE = "<="

# JSON field keys (avoid magic strings)
FIELD_NAME = "name"
FIELD_SYMBOL = "symbol"
FIELD_KIND = "kind"
FIELD_OP = "op"
FIELD_VALUE = "value"
FIELD_COOLDOWN = "cooldown_sec"
FIELD_LAST_TRIGGER_TS = "last_trigger_ts"

# Credential key names
ALPHAVANTAGE_API_KEY_KEY = "ALPHAVANTAGE_API_TOKEN"
FINNHUB_API_KEY_KEY = "FINNHUB_API_TOKEN"
