"""Główna logika wyszukiwarki duplikatów."""

from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import asdict
from pathlib import Path

from .decorators import measure_time
from .generators import duplicate_candidates, filter_extensions, iter_files
from .method_decorators import requires_directory
from .processes_cpu import parallel_cpu_fingerprints
from .regex_patterns import FilenameInfo, looks_like_copy, parse_filename
from .threading_io import parallel_hash_files

logger = logging.getLogger(__name__)


class DuplicateScanner:
    """Skaner katalogu wyszukujący identyczne pliki."""

    def __init__(self, root: str | Path, max_workers: int = 8, batch_size: int = 100) -> None:
        self.root = Path(root)
        self.max_workers = max_workers
        self.batch_size = batch_size
        self.last_error_count = 0

    @property
    def max_workers(self) -> int:
        """Liczba wątków używanych przy operacjach I/O."""
        return self._max_workers

    @max_workers.setter
    def max_workers(self, value: int) -> None:
        if value <= 0:
            raise ValueError("Liczba wątków musi być dodatnia.")
        self._max_workers = value

    @requires_directory
    @measure_time
    def scan(
        self,
        allowed_extensions: set[str] | None = None,
        use_cpu_processes: bool = True,
        process_workers: int = 4,
    ) -> dict:
        """Skanuje katalog i zwraca raport jako słownik."""
        if self.batch_size <= 0:
            raise ValueError("Rozmiar partii musi być dodatni.")
        if use_cpu_processes and process_workers <= 0:
            raise ValueError("Liczba procesów musi być dodatnia.")

        read_errors = 0

        def record_read_error(exc: OSError) -> None:
            nonlocal read_errors
            read_errors += 1
            logger.warning("Błąd podczas skanowania: %s", exc)

        root = self.root.resolve()
        files = filter_extensions(iter_files(root, record_read_error), allowed_extensions)
        files_scanned = 0
        parsed_names: dict[Path, FilenameInfo] = {}
        by_size: dict[int, list[Path]] = defaultdict(list)
        sizes: dict[Path, int] = {}
        for path in files:
            files_scanned += 1
            try:
                parsed_names[path] = parse_filename(path.name)
            except ValueError as exc:
                logger.warning("Pomijam analizę regex dla %s: %s", path, exc)

            try:
                size = path.stat().st_size
            except OSError as exc:
                record_read_error(exc)
                continue
            sizes[path] = size
            by_size[size].append(path)

        logger.info("Liczba plików do analizy: %d", files_scanned)
        candidates = (path for group in by_size.values() if len(group) > 1 for path in group)
        hashes, hash_errors = parallel_hash_files(candidates, self.max_workers, self.batch_size)
        read_errors += hash_errors

        by_hash: dict[tuple[int, str], list[Path]] = defaultdict(list)
        for path, digest in hashes.items():
            by_hash[(sizes[path], digest)].append(path)

        duplicate_groups = {
            key: sorted(group) for key, group in by_hash.items() if len(group) > 1
        }

        cpu_results: dict[Path, int] = {}
        if use_cpu_processes:
            duplicate_paths = list(duplicate_candidates(by_hash))
            if duplicate_paths:
                cpu_results = parallel_cpu_fingerprints(duplicate_paths, process_workers)
                read_errors += len(duplicate_paths) - len(cpu_results)

        duplicate_count = sum(len(group) for group in duplicate_groups.values())
        wasted_bytes = sum(
            (len(group) - 1) * size
            for (size, _), group in duplicate_groups.items()
        )
        self.last_error_count = read_errors

        return {
            "root": str(root),
            "files_scanned": files_scanned,
            "duplicate_groups": [
                {
                    "size": size,
                    "sha256": digest,
                    "files": [str(path) for path in group],
                    "cpu_fingerprints": {str(path): cpu_results.get(path) for path in group},
                    "filename_info": {
                        str(path): {
                            **(asdict(parsed_names[path]) if path in parsed_names else {}),
                            "looks_like_copy": looks_like_copy(path.name),
                        }
                        for path in group
                    },
                }
                for (size, digest), group in sorted(duplicate_groups.items())
            ],
            "duplicate_files": duplicate_count,
            "reclaimable_bytes": wasted_bytes,
            "read_errors": read_errors,
            "regex_parsed_files": len(parsed_names),
        }
