import json
import os
from pathlib import Path
from typing import Any, Dict
import re

from ..core.models import CacheConfig


def get_cache_dir(config: CacheConfig) -> Path:
    """Returns the cache directory, creating it if it doesn't exist."""
    cache_dir = Path(config.directory)
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def rotate_cache_files(config: CacheConfig) -> None:
    """Rotates cache files, keeping only the most recent ones."""
    cache_dir = get_cache_dir(config)
    # Get all rotated cache files and sort them by their sequence number in descending order
    rotated_files = []
    for file in cache_dir.glob("cache_data.*.json"):
        match = re.match(r"cache_data\.(\d+)\.json", file.name)
        if match:
            rotated_files.append((int(match.group(1)), file))
    
    # Sort by sequence number in descending order (newest first)
    rotated_files.sort(key=lambda x: x[0], reverse=True)
    
    # Keep only the most recent files according to max_files setting
    for seq_num, file in rotated_files[config.max_files - 1:]:
        file.unlink()


def get_latest_cache_file(config: CacheConfig) -> Path:
    """Gets the path to the latest cache file."""
    cache_dir = get_cache_dir(config)
    return cache_dir / "cache_data.json"


def save_to_cache(config: CacheConfig, data: Dict[str, Any]) -> None:
    """Merges and saves data to the cache file and handles rotation.

    This function preserves existing fields in the cache and only updates/merges
    keys present in `data` to avoid overwriting unrelated sections.
    """
    cache_file = get_latest_cache_file(config)

    # Load existing cache contents
    existing: Dict[str, Any] = {}
    if cache_file.exists():
        try:
            with open(cache_file, "r") as f:
                existing = json.load(f)
        except Exception:
            existing = {}

    # Shallow merge (top-level) — callers should provide full structures per key
    merged = dict(existing)
    for k, v in data.items():
        merged[k] = v

    # Handle rotation if size too big
    if cache_file.exists() and cache_file.stat().st_size > config.max_file_size:
        cache_dir = get_cache_dir(config)
        # Find the highest sequence number among existing rotated files
        max_seq = 0
        for file in cache_dir.glob("cache_data.*.json"):
            match = re.match(r"cache_data\.(\d+)\.json", file.name)
            if match:
                seq = int(match.group(1))
                max_seq = max(max_seq, seq)
        
        # Create new file name with next sequence number
        new_name = f"cache_data.{max_seq + 1}.json"
        cache_file.rename(cache_file.with_name(new_name))
        rotate_cache_files(config)

    with open(cache_file, "w") as f:
        json.dump(merged, f, indent=2)
