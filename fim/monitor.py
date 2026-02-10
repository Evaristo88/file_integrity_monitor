"""Monitoring and change detection logic."""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List

from .baseline import BaselineRecord
from .config import Config
from .utils import compute_file_hash, iter_files, should_exclude


@dataclass(frozen=True)
class Change:
    """Represents a change between baseline and current state."""

    change_type: str
    path: str
    details: Dict[str, str]


def snapshot(config: Config, logger) -> Dict[str, BaselineRecord]:
    """Create a fresh snapshot of current file state."""

    snapshot_data: Dict[str, BaselineRecord] = {}

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
                snapshot_data[str(path)] = record
            except OSError as exc:
                logger.warning("Skipping %s: %s", path, exc)

    return snapshot_data


def compare_baseline(
    baseline: Dict[str, BaselineRecord],
    current: Dict[str, BaselineRecord],
) -> List[Change]:
    """Compare baseline to the current snapshot and emit change objects."""

    baseline_paths = set(baseline.keys())
    current_paths = set(current.keys())

    changes: List[Change] = [
        Change(
            change_type="created",
            path=created_path,
            details={"hash": current[created_path].hash},
        )
        for created_path in sorted(current_paths - baseline_paths)
    ]

    changes.extend(
        Change(
            change_type="deleted",
            path=deleted_path,
            details={"hash": baseline[deleted_path].hash},
        )
        for deleted_path in sorted(baseline_paths - current_paths)
    )

    changes.extend(
        Change(
            change_type="modified",
            path=common_path,
            details={"before": baseline_record.hash, "after": current_record.hash},
        )
        for common_path in sorted(baseline_paths & current_paths)
        if (baseline_record := baseline[common_path]).hash
        != (current_record := current[common_path]).hash
    )

    return changes


def polling_loop(config: Config, baseline: Dict[str, BaselineRecord], reporter, logger) -> None:
    """Run periodic scans and report changes."""

    while True:
        current = snapshot(config, logger)
        changes = compare_baseline(baseline, current)
        reporter(changes)
        time.sleep(config.scan_interval_seconds)


def build_event_change(
    baseline: Dict[str, BaselineRecord],
    path: Path,
    config: Config,
    logger,
) -> Iterable[Change]:
    """Create a change list for a specific file path event."""

    if not path.exists():
        if str(path) in baseline:
            return [
                Change(
                    change_type="deleted",
                    path=str(path),
                    details={"hash": baseline[str(path)].hash},
                )
            ]
        return []

    try:
        file_hash = compute_file_hash(path, config.hash_algorithm)
        baseline_record = baseline.get(str(path))
        if baseline_record is None:
            return [Change(change_type="created", path=str(path), details={"hash": file_hash})]
        if baseline_record.hash != file_hash:
            return [
                Change(
                    change_type="modified",
                    path=str(path),
                    details={"before": baseline_record.hash, "after": file_hash},
                )
            ]
    except OSError as exc:
        logger.warning("Skipping %s: %s", path, exc)

    return []
