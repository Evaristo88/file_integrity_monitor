"""Configuration loading and validation."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import List


@dataclass(frozen=True)
class Config:
    """Typed configuration for the FIM."""

    paths: List[Path]
    exclude_globs: List[str]
    follow_symlinks: bool
    hash_algorithm: str
    baseline_file: Path
    log_file: Path
    scan_interval_seconds: int
    event_debounce_ms: int


def load_config(config_path: Path) -> Config:
    """Load config.json and normalize paths."""

    data = json.loads(config_path.read_text())

    paths = [Path(p).expanduser().resolve() for p in data.get("paths", [])]
    if not paths:
        raise ValueError("Config must include at least one path.")

    baseline_file = Path(data.get("baseline_file", "./baseline.json")).expanduser()
    log_file = Path(data.get("log_file", "./logs/fim.log")).expanduser()

    return Config(
        paths=paths,
        exclude_globs=list(data.get("exclude_globs", [])),
        follow_symlinks=bool(data.get("follow_symlinks", False)),
        hash_algorithm=str(data.get("hash_algorithm", "sha256")),
        baseline_file=baseline_file,
        log_file=log_file,
        scan_interval_seconds=int(data.get("scan_interval_seconds", 60)),
        event_debounce_ms=int(data.get("event_debounce_ms", 250)),
    )
