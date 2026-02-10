"""Baseline creation and persistence."""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict

from .config import Config
from .utils import compute_file_hash, iter_files, should_exclude


@dataclass(frozen=True)
class BaselineRecord:
    """Immutable record of a file's trusted state."""

    path: str
    hash: str
    size: int
    mtime: float


def build_baseline(config: Config, logger) -> Dict[str, BaselineRecord]:
    """Walk configured paths and compute a baseline hash for each file."""

    baseline: Dict[str, BaselineRecord] = {}

    for root in config.paths:
        for path in iter_files(root, config.follow_symlinks):
            if should_exclude(path, root, config.exclude_globs):
                continue

            try:
                file_hash = compute_file_hash(path, config.hash_algorithm)
                stat = path.stat()
                record = BaselineRecord(
                    path=str(path),
                    hash=file_hash,
                    size=stat.st_size,
                    mtime=stat.st_mtime,
                )
                baseline[str(path)] = record
            except OSError as exc:
                logger.warning("Skipping %s: %s", path, exc)

    return baseline


def save_baseline(records: Dict[str, BaselineRecord], destination: Path) -> None:
    """Save baseline records to a JSON file."""

    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = {path: asdict(record) for path, record in records.items()}
    destination.write_text(json.dumps(payload, indent=2, sort_keys=True))


def load_baseline(baseline_path: Path) -> Dict[str, BaselineRecord]:
    """Load baseline records from disk."""

    data = json.loads(baseline_path.read_text())
    baseline: Dict[str, BaselineRecord] = {}
    for path, record in data.items():
        baseline[path] = BaselineRecord(
            path=record["path"],
            hash=record["hash"],
            size=record["size"],
            mtime=record["mtime"],
        )
    return baseline
