"""Reporting helpers for output and logging."""

from __future__ import annotations

from typing import Iterable

from .monitor import Change


def format_change(change: Change) -> str:
    """Create a human-readable change description."""

    if change.change_type == "modified":
        return f"MODIFIED {change.path} before={change.details['before']} after={change.details['after']}"
    if change.change_type == "created":
        return f"CREATED {change.path} hash={change.details['hash']}"
    if change.change_type == "deleted":
        return f"DELETED {change.path} hash={change.details['hash']}"
    if change.change_type == "moved":
        return (
            f"MOVED {change.details['from']} -> {change.details['to']} hash={change.details.get('hash', '')}"
        )
    return f"{change.change_type.upper()} {change.path}"


def report_changes(changes: Iterable[Change], logger) -> None:
    """Emit change messages to the logger."""

    for change in changes:
        logger.info(format_change(change))
