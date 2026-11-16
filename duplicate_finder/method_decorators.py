"""Dekoratory metod wykorzystujące stan obiektu."""

from __future__ import annotations

import functools
from collections.abc import Callable
from typing import Any, Concatenate, ParamSpec, TypeVar

P = ParamSpec("P")
R = TypeVar("R")


def requires_directory(
    method: Callable[Concatenate[Any, P], R],
) -> Callable[Concatenate[Any, P], R]:
    """Sprawdza, czy ścieżka wskazuje istniejący katalog."""

    @functools.wraps(method)
    def wrapper(self: Any, /, *args: P.args, **kwargs: P.kwargs) -> R:
        if not self.root.exists():
            raise FileNotFoundError(f"Katalog nie istnieje: {self.root}")
        if not self.root.is_dir():
            raise NotADirectoryError(f"To nie jest katalog: {self.root}")
        return method(self, *args, **kwargs)

    return wrapper
