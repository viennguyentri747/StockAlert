import json
from pathlib import Path
from typing import Any, Dict, List, Tuple
from common import *
import re


def get_latest_cache_file(config: CacheConfig) -> Path:
    """Gets the path to the latest cache file."""
    cache_file = Path(config.directory) / config.file_name
    return cache_file


def _get_cache_file_components(config: CacheConfig) -> Tuple[Path, str, str, str]:
    """Extract reusable cache file components."""
    cache_dir = config.directory
    cache_file_name_no_ext = Path(config.file_name).stem
    cache_file_ext = Path(config.file_name).suffix
    pattern = f"{cache_file_name_no_ext}\\.(\\d+){re.escape(cache_file_ext)}"
    return cache_dir, cache_file_name_no_ext, cache_file_ext, pattern


def _get_rotated_files(config: CacheConfig) -> List[Tuple[int, Path]]:
    """Get all rotated cache files sorted by sequence number (newest first)."""
    cache_dir, cache_file_name_no_ext, cache_file_ext, pattern = _get_cache_file_components(config)

    rotated_files = []
    for file in cache_dir.glob(f"{cache_file_name_no_ext}.*{cache_file_ext}"):
        match = re.match(pattern, file.name)
        if match:
            rotated_files.append((int(match.group(1)), file))

    return sorted(rotated_files, key=lambda x: x[0], reverse=True)


def rotate_cache_files(config: CacheConfig) -> None:
    """Rotates cache files, keeping only the most recent ones."""
    rotated_files = _get_rotated_files(config)

    # Keep only the most recent files according to max_files setting
    for seq_num, file in rotated_files[config.max_files - 1:]:
        file.unlink()


def save_to_cache(config: CacheConfig, data: Dict[str, Any]) -> None:
    """Merges and saves data to the cache file and handles rotation.

    This function preserves existing fields in the cache and only updates/merges
    keys present in `data` to avoid overwriting unrelated sections.
    """
    LOG("saving to cache ...")
    latest_cache_file = get_latest_cache_file(config)

    # Load existing cache contents
    existing: Dict[str, Any] = {}
    if latest_cache_file.exists():
        try:
            with open(latest_cache_file, "r") as f:
                existing = json.load(f)
        except Exception:
            pass

    # Shallow merge (top-level) — callers should provide full structures per key
    merged = {**existing, **data}

    # Handle rotation if size too big
    if latest_cache_file.exists() and latest_cache_file.stat().st_size > config.max_file_size:
        cache_dir, cache_file_name_no_ext, cache_file_ext, _ = _get_cache_file_components(config)
        rotated_files = _get_rotated_files(config)

        # Get next sequence number
        max_seq = rotated_files[0][0] if rotated_files else 0
        new_name = f"{cache_file_name_no_ext}.{max_seq + 1}{cache_file_ext}"

        latest_cache_file.rename(latest_cache_file.with_name(new_name))
        rotate_cache_files(config)

    # Write merged data
    with open(latest_cache_file, "w") as f:
        LOG(f"writing to {latest_cache_file} ... {len(merged)} entries")
        json.dump(merged, f, indent=2)
