"""Wyrażenia regularne do analizy nazw plików."""

from __future__ import annotations

import re
from dataclasses import dataclass

FILENAME_RE = re.compile(
    r"^(?P<stem>.+?)(?:[_-](?P<date>\d{4}-\d{2}-\d{2}))?"
    r"(?:\.(?P<extension>[A-Za-z0-9]+))?$"
)

COPY_NAME_RE = re.compile(
    r"^(?P<base>.+?)[_-](?P<tag>copy|kopia|backup|bak)(?P<number>\d*)\.(?P<ext>[A-Za-z0-9]+)$",
    re.IGNORECASE,
)


@dataclass(frozen=True, slots=True)
class FilenameInfo:
    """Sparsowane informacje o nazwie pliku."""

    stem: str
    date: str | None
    extension: str | None


def parse_filename(name: str) -> FilenameInfo:
    """Parsuje nazwę pliku przy użyciu wzorca z grupami nazwanymi."""
    match = FILENAME_RE.fullmatch(name)
    if match is None:
        raise ValueError(f"Nieprawidłowa nazwa pliku: {name}")
    groups = match.groupdict()
    return FilenameInfo(
        stem=groups["stem"],
        date=groups["date"],
        extension=groups["extension"].lower() if groups["extension"] else None,
    )


def looks_like_copy(name: str) -> bool:
    """Sprawdza, czy nazwa wygląda jak nazwa kopii zapasowej."""
    return COPY_NAME_RE.fullmatch(name) is not None
