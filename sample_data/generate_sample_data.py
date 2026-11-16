"""Generuje mały, powtarzalny zbiór danych do demonstracji projektu."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parent / "generated"
NESTED = ROOT / "nested"


def main() -> None:
    """Zapisuje przykładowe pliki w katalogu generated."""
    NESTED.mkdir(parents=True, exist_ok=True)
    files = {
        ROOT / "dokument.txt": "To jest przykładowy dokument.\nLinia druga.\n",
        ROOT / "dokument_copy.txt": "To jest przykładowy dokument.\nLinia druga.\n",
        ROOT / "raport_2026-10-04.txt": "Raport uczelniany - Python.\n",
        ROOT / "raport_backup.txt": "Raport uczelniany - Python.\n",
        NESTED / "unikat.log": "INFO uruchomiono aplikację\nERROR przykładowy błąd\n",
        NESTED / "not_duplicate.txt": "Ten plik ma inną treść.\n",
    }
    for path, content in files.items():
        path.write_text(content, encoding="utf-8")
    print(f"Wygenerowano {len(files)} plików w {ROOT}")


if __name__ == "__main__":
    main()
