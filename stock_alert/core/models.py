import re
import time
from dataclasses import dataclass, asdict
from typing import Optional, Tuple
from dev_common.constants import AlertKind, Operation


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
    cooldown_sec: int = 300
    last_trigger_ts: Optional[float] = None

    def should_trigger(self, q: Quote, now_ts: float) -> Tuple[bool, str]:
        if self.kind == AlertKind.PRICE:
            lhs = q.price
        elif self.kind == AlertKind.PCT_DAY:
            lhs = q.pct_day
        elif self.kind == AlertKind.VOLUME:
            lhs = q.volume
        else:
            return False, f"Unsupported alert kind: {self.kind}"

        if self.op == Operation.GE:
            cond = lhs >= self.value
        elif self.op == Operation.LE:
            cond = lhs <= self.value
        else:
            return False, f"Unsupported operator: {self.op}"

        if cond and self.last_trigger_ts is not None:
            if now_ts - self.last_trigger_ts < self.cooldown_sec:
                return False, "Cooldown active"

        if cond:
            return True, f"{self.kind.value} {self.op.value} {self.value} (now {lhs})"
        return False, "Condition not met"


_KINDS_PATTERN = "|".join(k.value for k in AlertKind)
ALERT_RE = re.compile(
    rf"^({_KINDS_PATTERN})\s*(>=|<=)\s*(-?\d+(?:\.\d+)?)$",
    re.IGNORECASE,
)


def parse_condition(cond: str) -> Tuple[AlertKind, Operation, float]:
    m = ALERT_RE.match(cond.strip())
    if not m:
        raise ValueError(
            "Condition must be like: 'price >= 200', 'pct_day <= -3', or 'volume >= 1000000'"
        )
    kind_s, op_s, value = m.group(1).lower(), m.group(2), float(m.group(3))
    kind = AlertKind(kind_s)
    op = Operation(op_s)
    return kind, op, value
