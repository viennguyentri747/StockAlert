import json
import os
from dataclasses import asdict
from typing import Any, Dict, List

from ..common.constants import *
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


def load_config() -> Dict[str, Any]:
    ensure_app_dir()
    return _load_json(
        _path(CONFIG_FILE), {ALERT_FIELD_ALERTS: {}, ALERT_FIELD_WATCHLIST: []}
    )


def save_config(config: Dict[str, Any]):
    ensure_app_dir()
    _save_json(_path(CONFIG_FILE), config)


def load_watchlist() -> List[str]:
    config = load_config()
    data = config.get(ALERT_FIELD_WATCHLIST, [])
    return [s.upper() for s in data] if isinstance(data, list) else []


def save_watchlist(symbols: List[str]):
    config = load_config()
    config[ALERT_FIELD_WATCHLIST] = sorted(set(s.upper() for s in symbols))
    save_config(config)


def load_alerts() -> Dict[str, Dict]:
    config = load_config()
    return config.get(ALERT_FIELD_ALERTS, {})


def save_alerts(alerts: Dict[str, Dict]):
    config = load_config()
    config[ALERT_FIELD_ALERTS] = alerts
    save_config(config)


def alerts_from_dict(d: Dict[str, Dict]) -> Dict[str, Alert]:
    out: Dict[str, Alert] = {}
    for name, payload in d.items():
        out[name] = Alert.from_dict(payload)
    return out


def alerts_to_dict(alerts: Dict[str, Alert]) -> Dict[str, Dict]:
    return {name: a.to_dict() for name, a in alerts.items()}
