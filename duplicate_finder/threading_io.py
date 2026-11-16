"""Współbieżne zadania I/O wykonywane za pomocą wątków."""

from __future__ import annotations

import logging
import threading
from collections.abc import Iterable
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from .hashing import sha256_file
from .iterators import FileBatchIterator

logger = logging.getLogger(__name__)


def parallel_hash_files(
    paths: Iterable[Path], max_workers: int = 8, batch_size: int = 100
) -> tuple[dict[Path, str], int]:
    """Liczy SHA-256 plików współbieżnie.

    Zastosowano Lock do bezpiecznej aktualizacji współdzielonego licznika błędów.
    """
    results: dict[Path, str] = {}
    errors = 0
    lock = threading.Lock()

    def worker(path: Path) -> tuple[Path, str | None]:
        nonlocal errors
        try:
            return path, sha256_file(path)
        except (OSError, ValueError) as exc:
            logger.error("Nie można odczytać %s: %s", path, exc)
            with lock:
                errors += 1
            return path, None

    with ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="hash") as pool:
        for batch in FileBatchIterator(paths, batch_size):
            for path, digest in pool.map(worker, batch):
                if digest is not None:
                    results[path] = digest

    return results, errors
