from dataclasses import dataclass, asdict
from typing import Optional, Tuple, Dict, Any
from datetime import datetime
from .utils import *
from .constants import *


@dataclass
class CacheConfig:
    file_name: str
    directory: str
    max_files: int
    max_file_size: int

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "CacheConfig":
        return cls(
            file_name=d[CACHE_FIELD_FILE_NAME],
            directory=f"{DEFAULT_STORAGE_DIR_PATH}/{d[CACHE_FIELD_DIR_REL_PATH_VS_STORAGE]}",
            max_files=d[CACHE_FIELD_MAX_FILES],
            max_file_size=d[CACHE_FIELD_MAX_FILE_SIZE],
        )


@dataclass
class Quote:
    symbol: str
    price: float
    pct_day: float
    volume: int = 0


@dataclass
class Alert:
    name: str
    symbol: str
    kind: AlertKind
    op: Operation
    value: float
    alert_cooldown_secs: int = 300

    def __init__(self, symbol: str, kind: AlertKind, op: Operation,
                 value: float, alert_cooldown_secs: int = 300):
        """Initialize Alert with validation or custom logic."""
        self.symbol = symbol
        self.kind = kind
        self.op = op
        self.value = value
        self.alert_cooldown_secs = alert_cooldown_secs
        self.name = f"{self.symbol} {self.kind.value} {self.op.value} {self.value}"

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Alert":
        # Now calls the __init__ method through the constructor
        return cls(
            symbol=d[ALERT_FIELD_SYMBOL],
            kind=AlertKind(d[ALERT_FIELD_KIND]),
            op=Operation(d[ALERT_FIELD_OP]),
            value=d[ALERT_FIELD_VALUE],
            alert_cooldown_secs=d[ALERT_FIELD_ALERT_COOLDOWN],
        )

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d[ALERT_FIELD_KIND] = self.kind.value
        d[ALERT_FIELD_OP] = self.op.value
        return d

    def should_trigger(self, q: Quote, now_ts: float, last_trigger_ts: Optional[float] = None, last_alert_info: Optional[Dict[str, Any]] = None, ) -> Tuple[bool, str]:
        # Setup value
        if self.kind == AlertKind.PRICE_VALUE:
            new_value = q.price
        elif self.kind == AlertKind.PCT_DAY:
            new_value = q.pct_day
        elif self.kind == AlertKind.VOLUME:
            new_value = q.volume
        elif self.kind == AlertKind.PRICE_VALUE_OFFSET_SINCE_LAST_ALERT:
            if not last_alert_info or CACHE_FIELD_ALERT_LAST_PRICE not in last_alert_info:
                # If no last alert info, compared with price value change today (vs yesterday)
                LOG(f"No last alert info: {q.symbol}")
                if q.pct_day == 0:
                    new_value = 0  # No change from yesterday
                else:
                    yesterday_price = q.price / (1 + q.pct_day / 100)  # Yesterday's price based on day pct change
                    new_value = q.price - yesterday_price
            else:
                prev_price = float(last_alert_info[CACHE_FIELD_ALERT_LAST_PRICE])  # last alerted price
                new_value = q.price - prev_price
        elif self.kind == AlertKind.PRICE_PERCENT_OFFSET_SINCE_LAST_ALERT:
            if not last_alert_info or CACHE_FIELD_ALERT_LAST_PRICE not in last_alert_info:
                # If no last alert info, compared with price pct change today
                LOG(f"No last alert info: {q.symbol}")
                new_value = q.pct_day
            else:
                prev_price = float(last_alert_info[CACHE_FIELD_ALERT_LAST_PRICE])  # last alerted price
                if prev_price == 0:
                    return False, "Previous price is zero"
                new_value = ((q.price - prev_price) / prev_price) * 100
                LOG(f"Previous price: {prev_price}, Current price: {q.price}, Pct change: {new_value}")
        else:
            return False, f"Unsupported alert kind: {self.kind}"

        # Check condition on values
        if self.op == Operation.GE:
            cond = new_value >= self.value
        elif self.op == Operation.LE:
            cond = new_value <= self.value
        else:
            return False, f"Unsupported operator: {self.op}"

        if cond and last_trigger_ts is not None:
            # Handle both Unix timestamp (float) and human-readable timestamp (string) formats
            if isinstance(last_trigger_ts, str):
                try:
                    # Try to parse the human-readable timestamp
                    last_trigger_datetime = datetime.strptime(last_trigger_ts, "%Y-%m-%d %H:%M:%S")
                    last_trigger_unix = last_trigger_datetime.timestamp()
                except ValueError:
                    # If parsing fails, assume it's an old format and use 0 as default
                    last_trigger_unix = 0
            else:
                # It's already a Unix timestamp
                last_trigger_unix = last_trigger_ts

            if now_ts - last_trigger_unix < self.alert_cooldown_secs:
                return False, f"Condition met {new_value} {self.op.value} {self.value}, but cooldown is active -> Not triggering!"

        if cond:
            if self.kind == AlertKind.PRICE_VALUE_OFFSET_SINCE_LAST_ALERT:
                # Include more context for delta-based alerts
                return True, (f"{self.kind.value} {self.op.value} {self.value} " f"(delta {new_value})")
            elif self.kind == AlertKind.PRICE_PERCENT_OFFSET_SINCE_LAST_ALERT:
                return True, f"{self.kind.value} {self.op.value} {self.value} (now {new_value:.2f}%)"
            return True, f"{self.kind.value} {self.op.value} {self.value} (now {new_value})"
        return False, "Condition not met"
