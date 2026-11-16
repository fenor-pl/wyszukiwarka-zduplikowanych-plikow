"""Operacje I/O związane z plikami i obliczaniem SHA-256."""

from __future__ import annotations

import hashlib
from pathlib import Path

from .decorators import retry


@retry(attempts=3, delay=0.05, exceptions=(OSError,))
def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    """Oblicza SHA-256 pliku, czytając go blokami."""
    if chunk_size <= 0:
        raise ValueError("Rozmiar bloku musi być dodatni.")
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()
