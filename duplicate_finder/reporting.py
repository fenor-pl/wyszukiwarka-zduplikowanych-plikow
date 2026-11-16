"""Zapisywanie i prezentacja raportów."""

from __future__ import annotations

import json
from pathlib import Path


def save_json(report: dict, output: Path) -> None:
    """Zapisuje raport do pliku JSON."""
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")


def print_report(report: dict) -> None:
    """Drukuje najważniejsze informacje raportu."""
    print("\n=== RAPORT WYSZUKIWANIA DUPLIKATÓW ===")
    print(f"Katalog: {report['root']}")
    print(f"Pliki przeskanowane: {report['files_scanned']}")
    print(f"Grupy duplikatów: {len(report['duplicate_groups'])}")
    print(f"Pliki w grupach: {report['duplicate_files']}")
    print(f"Rozmiar nadmiarowych plików: {report['reclaimable_bytes']} B")
    print(f"Błędy odczytu: {report['read_errors']}")
    print(f"Nazwy rozpoznane: {report['regex_parsed_files']}")

    for index, group in enumerate(report["duplicate_groups"], start=1):
        print(f"\nGrupa {index} | {group['size']} B | SHA-256: {group['sha256']}")
        filename_info = group.get("filename_info", {})
        for path in group["files"]:
            info = filename_info.get(path, {})
            label = " (nazwa sugeruje kopię)" if info.get("looks_like_copy") else ""
            print(f"  - {path}{label}")
