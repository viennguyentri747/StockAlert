import json
from pathlib import Path
from typing import Any, Dict, List, Tuple
from stock_alert.common import *
import re


def get_latest_cache_file(config: CacheConfig) -> Path:
    """Gets the path to the latest cache file."""
    cache_file = Path(config.directory) / config.file_name
    return cache_file


def _get_cache_file_components(config: CacheConfig) -> Tuple[Path, str, str, str]:
    """Extract reusable cache file components."""
    cache_dir = Path(config.directory)
    cache_file_name_no_ext = Path(config.file_name).stem
    cache_file_ext = Path(config.file_name).suffix
    pattern = f"{cache_file_name_no_ext}\\.(\\d+){re.escape(cache_file_ext)}"
    return cache_dir, cache_file_name_no_ext, cache_file_ext, pattern


def _get_sorted_cache_files(config: CacheConfig) -> List[Tuple[int, Path]]:
    """Get all rotated cache files sorted by sequence number from extension (newest first)."""
    cache_dir, cache_file_name_no_ext, cache_file_ext, pattern = _get_cache_file_components(config)

    rotated_files: List[Tuple[int, Path]] = [] # (int: seq from file extension , Path: path to file)
    for file in cache_dir.glob(f"{cache_file_name_no_ext}.*{cache_file_ext}"):
        match = re.match(pattern, file.name)
        if match:
            rotated_files.append((int(match.group(1)), file))

    return sorted(rotated_files, key=lambda x: x[0], reverse=True)


def rotate_cache_files(config: CacheConfig) -> None:
    """Rotate cache files using simple sequential renaming."""
    cache_dir, name_no_ext, ext, _ = _get_cache_file_components(config)
    base_file = cache_dir / config.file_name
    
    # If max_files <= 1, just clean up rotated files
    if config.max_files <= 1:
        for f in cache_dir.glob(f"{name_no_ext}.*{ext}"):
            if f != base_file:
                f.unlink(missing_ok=True)
        return
    
    max_rotated = config.max_files - 1
    # Delete the oldest file if it exists
    oldest = cache_dir / f"{name_no_ext}.{max_rotated}{ext}"
    oldest.unlink(missing_ok=True)
    
    # Shift existing files: .1 -> .2, .2 -> .3, etc.
    max_seq_number = max_rotated
    min_seq_number = 1
    for new_index in range(max_seq_number, min_seq_number, -1): #new index range: [min_seq + 1, max_seq]
        old_index = new_index - 1
        src = cache_dir / f"{name_no_ext}.{old_index}{ext}" # -1 to get previous file, min_seq is exclusive (+1)
        dst = cache_dir / f"{name_no_ext}.{new_index}{ext}"
        if src.exists():
            src.replace(dst)
    
    # Move base file to .1
    if base_file.exists():
        dst = cache_dir / f"{name_no_ext}.1{ext}"
        base_file.replace(dst)


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
        # Perform bounded rotation with shifting; this renames the current file to .1 and shifts others.
        rotate_cache_files(config)

    # Write merged data (creates/overwrites the base file after rotation)
    with open(latest_cache_file, "w") as f:
        LOG(f"writing to {latest_cache_file} ... {len(merged)} entries")
        json.dump(merged, f, indent=2)
