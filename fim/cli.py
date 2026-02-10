"""Command line interface for the FIM."""

from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path
from threading import Event, Thread

from .baseline import build_baseline, load_baseline, save_baseline
from .config import load_config
from .monitor import (
    Change,
    build_event_change,
    compare_baseline,
    snapshot,
)
from .reporting import report_changes


def setup_logging(log_path: Path) -> logging.Logger:
    """Configure a console + file logger."""

    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("fim")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")

    file_handler = logging.FileHandler(log_path)
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


def run_baseline(config_path: Path) -> int:
    """Create and save a baseline."""

    config = load_config(config_path)
    logger = setup_logging(config.log_file)
    baseline = build_baseline(config, logger)
    save_baseline(baseline, config.baseline_file)
    logger.info("Baseline saved to %s", config.baseline_file)
    return 0


def run_scan(config_path: Path) -> int:
    """Run a one-time scan against the baseline."""

    config = load_config(config_path)
    logger = setup_logging(config.log_file)
    baseline = load_baseline(config.baseline_file)
    current = snapshot(config, logger)
    changes = compare_baseline(baseline, current)
    report_changes(changes, logger)
    logger.info("Scan complete. %d change(s) detected.", len(changes))
    return 0


def run_watch(config_path: Path, mode: str) -> int:
    """Watch for changes using inotify, polling, or both."""

    config = load_config(config_path)
    logger = setup_logging(config.log_file)
    baseline = load_baseline(config.baseline_file)

    stop_event = Event()

    def polling_worker() -> None:
        while not stop_event.is_set():
            current = snapshot(config, logger)
            changes = compare_baseline(baseline, current)
            report_changes(changes, logger)
            stop_event.wait(config.scan_interval_seconds)

    if mode in {"polling", "both"}:
        thread = Thread(target=polling_worker, daemon=True)
        thread.start()

    if mode in {"realtime", "both"}:
        try:
            from watchdog.events import FileSystemEventHandler
            from watchdog.observers import Observer
        except ImportError:
            logger.error("watchdog is required for realtime mode. Install with pip.")
            return 1

        class Handler(FileSystemEventHandler):
            """Translate filesystem events into change reports."""

            def __init__(self) -> None:
                super().__init__()
                self._last_event = {}

            def _debounced(self, path: Path) -> bool:
                now = time.monotonic()
                last = self._last_event.get(str(path), 0)
                if (now - last) * 1000 < config.event_debounce_ms:
                    return True
                self._last_event[str(path)] = now
                return False

            def on_any_event(self, event) -> None:
                if event.is_directory:
                    return

                path = Path(event.src_path)
                if self._debounced(path):
                    return

                changes = list(build_event_change(baseline, path, config, logger))
                report_changes(changes, logger)

            def on_moved(self, event) -> None:
                if event.is_directory:
                    return

                change = Change(
                    change_type="moved",
                    path=event.dest_path,
                    details={"from": event.src_path, "to": event.dest_path},
                )
                report_changes([change], logger)

        observer = Observer()
        handler = Handler()
        for root in config.paths:
            observer.schedule(handler, str(root), recursive=True)
        observer.start()

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            stop_event.set()
            observer.stop()
            observer.join()
            return 0

    logger.info("Polling active. Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        stop_event.set()
        return 0


def build_parser() -> argparse.ArgumentParser:
    """Create the CLI argument parser."""

    parser = argparse.ArgumentParser(description="File Integrity Monitor")
    parser.add_argument("--config", required=True, help="Path to config.json")

    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("baseline", help="Create a baseline")
    subparsers.add_parser("scan", help="Run a one-time scan")

    watch_parser = subparsers.add_parser("watch", help="Watch for changes")
    watch_parser.add_argument(
        "--mode",
        choices=["polling", "realtime", "both"],
        default="both",
        help="Choose polling, realtime, or both",
    )

    return parser


def main() -> None:
    """CLI entrypoint."""

    parser = build_parser()
    args = parser.parse_args()

    config_path = Path(args.config).expanduser().resolve()

    if args.command == "baseline":
        sys.exit(run_baseline(config_path))
    if args.command == "scan":
        sys.exit(run_scan(config_path))
    if args.command == "watch":
        sys.exit(run_watch(config_path, args.mode))


if __name__ == "__main__":
    main()
