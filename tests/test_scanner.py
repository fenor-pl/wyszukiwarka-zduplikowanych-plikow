from __future__ import annotations

import tempfile
import unittest
from hashlib import sha256
from pathlib import Path
from unittest.mock import patch

from duplicate_finder.processes_cpu import parallel_cpu_fingerprints
from duplicate_finder.scanner import DuplicateScanner


class TestScanner(unittest.TestCase):
    def test_duplicate_detection(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            original = root / "one_2026-10-04.txt"
            copy = root / "two_copy.txt"
            content = b"same content\n"
            original.write_bytes(content)
            copy.write_bytes(content)
            (root / "unique.txt").write_bytes(b"diff content\n")

            report = DuplicateScanner(root, max_workers=2, batch_size=1).scan(process_workers=2)
            self.assertEqual(report["files_scanned"], 3)
            self.assertEqual(report["duplicate_files"], 2)
            self.assertEqual(len(report["duplicate_groups"]), 1)
            self.assertEqual(report["reclaimable_bytes"], len(content))
            self.assertEqual(report["read_errors"], 0)
            group = report["duplicate_groups"][0]
            self.assertEqual(group["sha256"], sha256(content).hexdigest())
            self.assertEqual(group["files"], [str(original), str(copy)])
            self.assertEqual(group["filename_info"][str(original)]["date"], "2026-10-04")
            self.assertTrue(group["filename_info"][str(copy)]["looks_like_copy"])
            first_fingerprint = group["cpu_fingerprints"][str(original)]
            self.assertIsInstance(first_fingerprint, int)
            self.assertEqual(group["cpu_fingerprints"][str(copy)], first_fingerprint)

    def test_directory_read_error_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            scanner = DuplicateScanner(tmp)
            with (
                patch("duplicate_finder.generators.os.scandir", side_effect=PermissionError(tmp)),
                self.assertLogs("duplicate_finder.scanner", level="WARNING"),
            ):
                report = scanner.scan(use_cpu_processes=False)

            self.assertEqual(report["files_scanned"], 0)
            self.assertEqual(report["read_errors"], 1)
            self.assertEqual(scanner.last_error_count, 1)

    def test_process_pool_keeps_results_when_one_file_cannot_be_read(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            file = root / "one.txt"
            file.write_bytes(b"A")

            with self.assertLogs("duplicate_finder.processes_cpu", level="WARNING"):
                fingerprints = parallel_cpu_fingerprints([root / "missing.txt", file], max_workers=2)
            self.assertEqual(fingerprints, {file: 65})
