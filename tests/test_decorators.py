from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from duplicate_finder.decorators import retry
from duplicate_finder.scanner import DuplicateScanner


class TestDecorators(unittest.TestCase):
    def test_retry_repeats_and_returns(self) -> None:
        state = {"calls": 0}

        @retry(attempts=3, delay=0)
        def flaky() -> str:
            state["calls"] += 1
            if state["calls"] < 3:
                raise OSError("temporary")
            return "ok"

        with self.assertLogs("duplicate_finder.decorators", level="WARNING"):
            self.assertEqual(flaky(), "ok")
        self.assertEqual(state["calls"], 3)
        self.assertEqual(flaky.__name__, "flaky")

    def test_property_validation(self) -> None:
        scanner = DuplicateScanner(".")
        with self.assertRaises(ValueError):
            scanner.max_workers = 0

    def test_directory_is_required(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            file = Path(tmp) / "file.txt"
            file.touch()
            with self.assertRaises(NotADirectoryError):
                DuplicateScanner(file).scan()
