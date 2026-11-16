from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from duplicate_finder.generators import iter_files
from duplicate_finder.iterators import FileBatchIterator


class TestIteratorGenerator(unittest.TestCase):
    def test_batches(self) -> None:
        batches = list(FileBatchIterator(range(5), 2))
        self.assertEqual(batches, [[0, 1], [2, 3], [4]])

    def test_generator_walks_tree(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a.txt").write_text("a", encoding="utf-8")
            child = root / "child"
            child.mkdir()
            (child / "b.txt").write_text("b", encoding="utf-8")
            found = {path.name for path in iter_files(root)}
            self.assertEqual(found, {"a.txt", "b.txt"})
