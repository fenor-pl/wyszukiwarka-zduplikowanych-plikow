"""Generatory do leniwego skanowania drzewa katalogów."""

from __future__ import annotations

import os
from collections.abc import Callable, Generator, Iterable
from pathlib import Path


def iter_files(
    root: Path, on_error: Callable[[OSError], None] | None = None
) -> Generator[Path, None, None]:
    """Zwraca kolejne pliki w drzewie katalogu i zgłasza błędy odczytu."""
    try:
        with os.scandir(root) as entries:
            for entry in entries:
                path = Path(entry.path)
                try:
                    if entry.is_dir(follow_symlinks=False):
                        yield from iter_files(path, on_error)
                    elif entry.is_file(follow_symlinks=False):
                        yield path
                except OSError as exc:
                    if on_error is not None:
                        on_error(exc)
    except OSError as exc:
        if on_error is not None:
            on_error(exc)


def filter_extensions(
    paths: Iterable[Path], allowed_extensions: set[str] | None
) -> Generator[Path, None, None]:
    """Filtruje pliki po rozszerzeniach w sposób leniwy."""
    if not allowed_extensions:
        yield from paths
        return

    normalized = {ext.lower().lstrip(".") for ext in allowed_extensions}
    for path in paths:
        suffix = path.suffix.lower().lstrip(".")
        if suffix in normalized:
            yield path


def duplicate_candidates(groups: dict[tuple[int, str], list[Path]]) -> Generator[Path, None, None]:
    """Zwraca pliki należące do grup duplikatów."""
    for paths in groups.values():
        if len(paths) > 1:
            yield from paths
