from enum import Enum
from pathlib import Path

# FORMATS
LINE_SEPARATOR = f"\n{'=' * 60}\n"
LINE_SEPARATOR_NO_ENDLINE = f"{'=' * 60}"


# Data filenames
CONFIG_FILE_REL_PATH_VS_SRORAGE = "configs/current_config.json"

DEFAULT_MONITOR_INTERVAL = "15s"
DEFAULT_COOLDOWN_SEC = 300

REPO_PATH = Path.home() / "stock_alert/"
DEFAULT_STORAGE_DIR_PATH = f"{REPO_PATH}/.stockalert"
CREDENTIALS_FILE_PATH = f"{REPO_PATH}/.my_credentials.env"


class AlertKind(str, Enum):
    PRICE_VALUE = "price_value"
    VOLUME = "volume"
    PCT_DAY = "price_percent_day"
    PRICE_VALUE_OFFSET_SINCE_LAST_ALERT = "price_value_offset_since_last_alert"
    PRICE_PERCENT_OFFSET_SINCE_LAST_ALERT = "price_percent_offset_since_last_alert"


class Operation(str, Enum):
    GE = ">="
    LE = "<="


ALERT_LOG_TAG = "[ALERT]"

# JSON field keys (avoid magic strings)
ALERT_FIELD_SYMBOL = "symbol"
ALERT_FIELD_KIND = "kind"
ALERT_FIELD_VALUE = "value"
ALERT_FIELD_OP = "op"
ALERT_FIELD_ALERT_COOLDOWN = "alert_min_cooldown_secs"
ALERT_FIELD_ALERTS = "alerts"
ALERT_FIELD_WATCHLIST = "watchlist"

CACHE_FIELD_LAST_ALERTS_TRIGGER_TS = "last_alerts_trigger_ts"
CACHE_FIELD_ALERTS_HISTORY = "alerts"
CACHE_FIELD_ALERT_LAST_PRICE = "last_alert_price"

ALERT_RECORD_FIELD_TRIGGER_TS = "trigger_ts"
ALERT_RECORD_FIELD_NAME = "alert_name"

CACHE_FIELD_MAX_SIZE_BYTES = "max_size_bytes"
CACHE_FIELD_NUM_ROTATED_FILES = "num_rotated_files"

CACHE_FIELD_DIR_REL_PATH_VS_STORAGE = "rel_dir_path_vs_storage"
CACHE_FIELD_MAX_FILES = "max_files"
CACHE_FIELD_MAX_FILE_SIZE = "max_file_size"
CACHE_FIELD_FILE_NAME = "file_name"

# Credential key names
ALPHAVANTAGE_API_KEY = "ALPHAVANTAGE_API_TOKEN"
FINNHUB_API_KEY = "FINNHUB_API_TOKEN"
