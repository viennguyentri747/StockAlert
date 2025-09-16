import re
import time
from dataclasses import dataclass, asdict
from typing import Optional, Tuple, Dict, Any
from datetime import datetime

from ..common.constants import *


@dataclass
class CacheConfig:
    directory: str
    max_files: int
    max_file_size: int

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "CacheConfig":
        return cls(
            directory=d[CONFIG_FIELD_DIRECTORY],
            max_files=d[CONFIG_FIELD_MAX_FILES],
            max_file_size=d[CONFIG_FIELD_MAX_FILE_SIZE],
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

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Alert":
        return cls(
            name=d[ALERT_FIELD_NAME],
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

    def should_trigger(
        self,
        q: Quote,
        now_ts: float,
        last_trigger_ts: Optional[float] = None,
        last_alert_info: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bool, str]:
        # Setup value
        if self.kind == AlertKind.PRICE_VALUE:
            new_value = q.price
        elif self.kind == AlertKind.PCT_DAY:
            new_value = q.pct_day
        elif self.kind == AlertKind.VOLUME:
            new_value = q.volume
        elif self.kind == AlertKind.LAST_ALERT_PRICE_OFFSET_VALUE:
            if not last_alert_info or AlertKind.PRICE_VALUE.value not in last_alert_info:
                return False, "No prior alert data"
            prev_price = float(last_alert_info[AlertKind.PRICE_VALUE.value])  # last alerted price
            new_value = q.price - prev_price
        elif self.kind == AlertKind.LAST_ALERT_PRICE_OFFSET_PERCENT:
            if not last_alert_info or AlertKind.PRICE_VALUE.value not in last_alert_info:
                return False, "No prior alert data"
            prev_price = float(last_alert_info[AlertKind.PRICE_VALUE.value])  # last alerted price
            if prev_price == 0:
                return False, "Previous price is zero"
            new_value = ((q.price - prev_price) / prev_price) * 100
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
                return False, "Cooldown active"

        if cond:
            if self.kind == AlertKind.LAST_ALERT_PRICE_OFFSET_VALUE:
                # Include more context for delta-based alerts
                return True, (
                    f"{self.kind.value} {self.op.value} {self.value} "
                    f"(delta {new_value})"
                )
            elif self.kind == AlertKind.LAST_ALERT_PRICE_OFFSET_PERCENT:
                return True, f"{self.kind.value} {self.op.value} {self.value} (now {new_value:.2f}%)"
            return True, f"{self.kind.value} {self.op.value} {self.value} (now {new_value})"
        return False, "Condition not met"


# Update the regex pattern to include the new alert kinds
_KINDS_PATTERN = "|".join(k.value for k in AlertKind)
ALERT_RE = re.compile(
    rf"^({_KINDS_PATTERN})\s*(>=|<=)\s*(-?\d+(?:\.\d+)?)$",
    re.IGNORECASE,
)


def parse_condition(cond: str) -> Tuple[AlertKind, Operation, float]:
    m = ALERT_RE.match(cond.strip())
    if not m:
        raise ValueError(
            f"Condition must be like: '{AlertKind.PRICE_VALUE.value} >= 200', '{AlertKind.PCT_DAY.value} <= -3', "
            f"'{AlertKind.VOLUME.value} >= 1000000', '{AlertKind.LAST_ALERT_PRICE_OFFSET_PERCENT.value} >= 5', "
        )
    kind_s, op_s, value = m.group(1).lower(), m.group(2), float(m.group(3))
    kind = AlertKind(kind_s)
    op = Operation(op_s)
    return kind, op, value
