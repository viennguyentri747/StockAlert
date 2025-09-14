import json
import os
from dataclasses import asdict
from typing import Dict, List
from dev_common.constants import (
    APP_DIR_ENV,
    DEFAULT_APP_DIR_NAME,
    WATCHLIST_FILE,
    ALERTS_FILE,
)
from dev_common.constants import (
    AlertKind,
    Operation,
    FIELD_KIND,
    FIELD_OP,
    FIELD_NAME,
)

from ..core import Alert


def get_app_dir() -> str:
    # Sandbox-friendly default; override with env via APP_DIR_ENV
    return os.environ.get(APP_DIR_ENV, os.path.join(os.getcwd(), DEFAULT_APP_DIR_NAME))


def ensure_app_dir():
    os.makedirs(get_app_dir(), exist_ok=True)


def _path(name: str) -> str:
    return os.path.join(get_app_dir(), name)


def _load_json(path: str, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return default


def _save_json(path: str, data):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)
    os.replace(tmp, path)


def load_watchlist() -> List[str]:
    ensure_app_dir()
    data = _load_json(_path(WATCHLIST_FILE), [])
    return [s.upper() for s in data]


def save_watchlist(symbols: List[str]):
    ensure_app_dir()
    _save_json(_path(WATCHLIST_FILE), sorted(set(s.upper() for s in symbols)))


def load_alerts() -> Dict[str, Dict]:
    ensure_app_dir()
    return _load_json(_path(ALERTS_FILE), {})


def save_alerts(alerts: Dict[str, Dict]):
    ensure_app_dir()
    _save_json(_path(ALERTS_FILE), alerts)


def alerts_from_dict(d: Dict[str, Dict]) -> Dict[str, Alert]:
    out: Dict[str, Alert] = {}
    for name, payload in d.items():
        k = payload.get(FIELD_KIND)
        o = payload.get(FIELD_OP)
        # Accept both enum values and legacy strings
        if isinstance(k, str):
            payload[FIELD_KIND] = AlertKind(k)
        if isinstance(o, str):
            payload[FIELD_OP] = Operation(o)
        out[name] = Alert(**payload)
    return out


def alerts_to_dict(alerts: Dict[str, Alert]) -> Dict[str, Dict]:
    result: Dict[str, Dict] = {}
    for name, a in alerts.items():
        d = asdict(a)
        # Convert enums to their values for JSON
        d[FIELD_KIND] = a.kind.value
        d[FIELD_OP] = a.op.value
        result[name] = d
    return result
