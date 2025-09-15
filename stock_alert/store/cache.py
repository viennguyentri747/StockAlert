import json
import os
from pathlib import Path
from typing import Any, Dict

from ..core.models import CacheConfig


def get_cache_dir(config: CacheConfig) -> Path:
    """Returns the cache directory, creating it if it doesn't exist."""
    cache_dir = Path(config.directory)
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def rotate_cache_files(config: CacheConfig) -> None:
    """Rotates cache files, keeping only the most recent ones."""
    cache_dir = get_cache_dir(config)
    files = sorted(cache_dir.glob("cache_data_*.json"), key=os.path.getmtime, reverse=True)
    for old_file in files[config.max_files - 1 :]:
        old_file.unlink()


def get_latest_cache_file(config: CacheConfig) -> Path:
    """Gets the path to the latest cache file."""
    cache_dir = get_cache_dir(config)
    return cache_dir / "cache_data.json"


def save_to_cache(config: CacheConfig, data: Dict[str, Any]) -> None:
    """Saves data to the cache file and handles rotation."""
    cache_file = get_latest_cache_file(config)

    if cache_file.exists() and cache_file.stat().st_size > config.max_file_size:
        timestamp = os.path.getmtime(cache_file)
        new_name = f"cache_data_{timestamp}.json"
        cache_file.rename(cache_file.with_name(new_name))
        rotate_cache_files(config)

    with open(cache_file, "w") as f:
        json.dump(data, f, indent=2)