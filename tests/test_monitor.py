"""Unit tests for monitor change detection."""

import unittest

from fim.baseline import BaselineRecord
from fim.monitor import compare_baseline


class CompareBaselineTests(unittest.TestCase):
    def test_compare_baseline_emits_created_deleted_modified(self) -> None:
        baseline = {
            "/path/deleted.txt": BaselineRecord(
                path="/path/deleted.txt",
                hash="oldhash",
                size=10,
                mtime=1.0,
            ),
            "/path/modified.txt": BaselineRecord(
                path="/path/modified.txt",
                hash="oldhash",
                size=11,
                mtime=2.0,
            ),
        }
        current = {
            "/path/created.txt": BaselineRecord(
                path="/path/created.txt",
                hash="newhash",
                size=12,
                mtime=3.0,
            ),
            "/path/modified.txt": BaselineRecord(
                path="/path/modified.txt",
                hash="newhash",
                size=11,
                mtime=4.0,
            ),
        }

        changes = compare_baseline(baseline, current)
        summary = [(change.change_type, change.path) for change in changes]

        self.assertEqual(
            summary,
            [
                ("created", "/path/created.txt"),
                ("deleted", "/path/deleted.txt"),
                ("modified", "/path/modified.txt"),
            ],
        )


if __name__ == "__main__":
    unittest.main()
