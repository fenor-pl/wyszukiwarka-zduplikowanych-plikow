"""Własne dekoratory używane w projekcie."""

from __future__ import annotations

import functools
import logging
import time
from collections.abc import Callable
from typing import ParamSpec, TypeVar

P = ParamSpec("P")
R = TypeVar("R")

logger = logging.getLogger(__name__)


def measure_time(func: Callable[P, R]) -> Callable[P, R]:
    """Mierzy czas wykonania funkcji i zapisuje wynik do logu."""

    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        logger.info("[%s] wykonano w %.4f s", func.__name__, elapsed)
        return result

    return wrapper


def retry(
    attempts: int = 3,
    delay: float = 0.1,
    exceptions: tuple[type[BaseException], ...] = (OSError,),
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Ponawia wykonanie funkcji po wybranych wyjątkach."""
    if attempts < 1:
        raise ValueError("Liczba prób musi być dodatnia.")
    if delay < 0:
        raise ValueError("Opóźnienie nie może być ujemne.")

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            for attempt in range(1, attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as exc:
                    logger.warning(
                        "%s: próba %d/%d nieudana: %s",
                        func.__name__,
                        attempt,
                        attempts,
                        exc,
                    )
                    time.sleep(delay)
            return func(*args, **kwargs)

        return wrapper

    return decorator
