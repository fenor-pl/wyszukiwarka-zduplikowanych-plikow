"""Równoległe zadania CPU-bound wykonywane w procesach."""

from __future__ import annotations

import logging
import multiprocessing
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

logger = logging.getLogger(__name__)


def cpu_fingerprint(path: Path, max_bytes: int = 256_000) -> int:
    """Oblicza 32-bitowy odcisk z początku pliku w czystym Pythonie."""
    with path.open("rb") as handle:
        data = handle.read(max_bytes)

    value = 0
    for byte in data:
        value = ((value << 5) - value + byte) & 0xFFFFFFFF
    return value


def parallel_cpu_fingerprints(paths: list[Path], max_workers: int = 4) -> dict[Path, int]:
    """Liczy odciski w puli procesów i pomija pliki z błędami odczytu."""
    results: dict[Path, int] = {}
    context = multiprocessing.get_context("spawn")
    with ProcessPoolExecutor(max_workers=max_workers, mp_context=context) as pool:
        futures = {pool.submit(cpu_fingerprint, path): path for path in paths}
        for future, path in futures.items():
            try:
                results[path] = future.result()
            except OSError as exc:
                logger.warning("Nie można obliczyć odcisku %s: %s", path, exc)
    return results
