# File Integrity Monitor (FIM)

A small, readable File Integrity Monitor that can baseline files, scan for changes, and optionally watch in real time on Linux using inotify (via `watchdog`). The design is deliberately simple and heavily documented so that someone new to the project can understand how it works.

## What this does

- Builds a baseline by hashing files (default SHA-256).
- Scans and reports changes (created, deleted, modified).
- Watches for real-time changes using inotify if available.
- Logs to console and to a file.

## Quick start

1. Create and activate a virtual environment (recommended).
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Build a baseline:

```bash
python -m fim --config config.json baseline
```

4. Run a one-time scan:

```bash
python -m fim --config config.json scan
```

5. Watch for changes (real time + periodic scan fallback):

```bash
python -m fim --config config.json watch --mode both
```

6. Run unit tests:

```bash
python -m unittest discover -s tests -p "test*.py" -v
```

## Configuration

All settings are in [config.json](config.json). The most important fields:

- `paths`: List of files/directories to monitor. Defaults to a safe sample folder.
- `exclude_globs`: Glob patterns to skip.
- `baseline_file`: Where to write the baseline JSON.
- `log_file`: Where to write logs.
- `scan_interval_seconds`: How often a polling scan runs.
- `event_debounce_ms`: Debounce window for file events.

Example (already included):

```json
{
  "paths": ["./sample_data"],
  "exclude_globs": ["**/*.tmp"],
  "follow_symlinks": false,
  "hash_algorithm": "sha256",
  "baseline_file": "./baseline.json",
  "log_file": "./logs/fim.log",
  "scan_interval_seconds": 60,
  "event_debounce_ms": 250
}
```

## How it works

1. **Baselining**: The `baseline` command walks each path, calculates a hash per file, and stores results in `baseline.json`.
2. **Scanning**: The `scan` command re-hashes files and compares with the baseline. Differences are reported as `created`, `deleted`, or `modified`.
3. **Watching**: The `watch` command uses inotify (Linux) when available. If you choose `--mode both`, it also runs periodic scans as a safety net.

## Directory layout

```
file_integrity_monitor/
  fim/
    __init__.py
    __main__.py
    baseline.py
    cli.py
    config.py
    monitor.py
    reporting.py
    utils.py
  logs/
  sample_data/
  config.json
  requirements.txt
```

## Notes and design choices

- Hashes are calculated for every file on each scan to prioritize integrity over speed.
- Baseline files are JSON so they are easy to inspect and audit.
- Real-time mode is optional and depends on `watchdog`. If it is missing, the tool warns and exits.

## Try it out

You can edit or add files under [sample_data](sample_data) to see alerts. For example:

```bash
echo "change" >> sample_data/example.txt
python -m fim --config config.json scan
```

## Troubleshooting

- If you see `watchdog is required`, install dependencies with `pip install -r requirements.txt`.
- If a path is not readable, it will be skipped and logged as a warning.

## License

MIT
