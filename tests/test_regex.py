from __future__ import annotations

import unittest

from duplicate_finder.regex_patterns import looks_like_copy, parse_filename


class TestRegex(unittest.TestCase):
    def test_named_groups_extract_data(self) -> None:
        parsed = parse_filename("raport_2026-10-04.txt")
        self.assertEqual(parsed.stem, "raport")
        self.assertEqual(parsed.date, "2026-10-04")
        self.assertEqual(parsed.extension, "txt")

    def test_copy_pattern(self) -> None:
        self.assertTrue(looks_like_copy("dokument_copy.txt"))
        self.assertTrue(looks_like_copy("plik-kopia2.pdf"))
        self.assertFalse(looks_like_copy("unikat.txt"))
