"""Shared helpers used across the project."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Iterable, Iterator


def compute_file_hash(path: Path, algorithm: str) -> str:
    """Compute a hex digest for a file using the chosen algorithm."""

    hasher = hashlib.new(algorithm)
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def should_exclude(path: Path, root: Path, exclude_globs: Iterable[str]) -> bool:
    """Return True if path matches any exclude glob (absolute or relative)."""

    relative = path.relative_to(root)
    for pattern in exclude_globs:
        if path.match(pattern) or relative.match(pattern):
            return True
    return False


def iter_files(root: Path, follow_symlinks: bool) -> Iterator[Path]:
    """Yield files under a root path, supporting single files and directories."""

    if root.is_file():
        yield root
        return

    for path in root.rglob("*"):
        if path.is_file() and (follow_symlinks or not path.is_symlink()):
            yield path
