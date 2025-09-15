import json
import os
from dataclasses import asdict
from typing import Dict, List

from ..common.constants import (
    ALERTS_FILE,
    DEFAULT_APP_DIR_PATH,
    WATCHLIST_FILE,
)
from ..core import Alert


def ensure_app_dir():
    os.makedirs(DEFAULT_APP_DIR_PATH, exist_ok=True)


def _path(name: str) -> str:
    return os.path.join(DEFAULT_APP_DIR_PATH, name)


def _load_json(path: str, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def _save_json(path: str, data):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)
    os.replace(tmp, path)


def load_watchlist() -> List[str]:
    ensure_app_dir()
    data = _load_json(_path(WATCHLIST_FILE), [])
    return [s.upper() for s in data] if isinstance(data, list) else []


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
        out[name] = Alert.from_dict(payload)
    return out


def alerts_to_dict(alerts: Dict[str, Alert]) -> Dict[str, Dict]:
    return {name: a.to_dict() for name, a in alerts.items()}
