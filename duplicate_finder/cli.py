"""Interfejs wiersza poleceń aplikacji."""

from __future__ import annotations

import argparse
import logging
from concurrent.futures.process import BrokenProcessPool
from pathlib import Path

from .gil_benchmark import format_benchmark, run_gil_benchmark
from .reporting import print_report, save_json
from .scanner import DuplicateScanner


def build_parser() -> argparse.ArgumentParser:
    """Definiuje polecenia skanowania i pomiaru GIL."""
    parser = argparse.ArgumentParser(description="Wyszukuje pliki o tej samej zawartości.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    scan = subparsers.add_parser("scan", help="Przeskanuj katalog")
    scan.add_argument("path", type=Path, help="Katalog do przeskanowania")
    scan.add_argument("--ext", nargs="+", help="Opcjonalne rozszerzenia, np. txt jpg png")
    scan.add_argument("--threads", type=int, default=8, help="Liczba wątków do I/O")
    scan.add_argument("--processes", type=int, default=4, help="Liczba procesów CPU")
    scan.add_argument("--batch-size", type=int, default=100, help="Liczba plików w partii do obliczania SHA-256")
    scan.add_argument("--output", type=Path, default=Path("reports/duplicates.json"))
    scan.add_argument("--no-processes", action="store_true", help="Wyłącz analizę CPU w procesach")

    gil = subparsers.add_parser("gil", help="Uruchom benchmark GIL")
    gil.add_argument("--iterations", type=int, default=5_000_000)
    gil.add_argument("--workers", type=int, default=4)
    gil.add_argument("--output", type=Path, default=Path("reports/gil.json"))

    return parser


def main() -> int:
    """Uruchamia wybrane polecenie i zapisuje raport."""
    parser = build_parser()
    args = parser.parse_args()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(threadName)s | %(message)s",
    )

    try:
        if args.command == "scan":
            scanner = DuplicateScanner(args.path, max_workers=args.threads, batch_size=args.batch_size)
            report = scanner.scan(
                allowed_extensions=set(args.ext) if args.ext else None,
                use_cpu_processes=not args.no_processes,
                process_workers=args.processes,
            )
            print_report(report)
        else:
            report = run_gil_benchmark(iterations=args.iterations, workers=args.workers)
            print(format_benchmark(report))
        save_json(report, args.output)
    except (OSError, ValueError, BrokenProcessPool) as exc:
        parser.exit(2, f"Błąd: {exc}\n")
    print(f"\nZapisano raport: {args.output}")
    return 0
