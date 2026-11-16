"""Własny iterator używany do przetwarzania plików partiami."""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from typing import TypeVar

T = TypeVar("T")


class FileBatchIterator(Iterator[list[T]]):
    """Iterator zwracający kolejne partie elementów o ustalonej wielkości."""

    def __init__(self, items: Iterable[T], batch_size: int) -> None:
        if batch_size <= 0:
            raise ValueError("batch_size musi być dodatni")
        self._iterator = iter(items)
        self._batch_size = batch_size

    def __iter__(self) -> "FileBatchIterator[T]":
        return self

    def __next__(self) -> list[T]:
        batch: list[T] = []
        for _ in range(self._batch_size):
            try:
                batch.append(next(self._iterator))
            except StopIteration:
                break
        if not batch:
            raise StopIteration
        return batch
