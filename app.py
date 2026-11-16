"""Punkt startowy projektu."""

import sys


def main() -> int:
    """Sprawdza wersję Pythona i uruchamia interfejs."""
    if sys.version_info < (3, 12):
        sys.exit("Wymagany jest Python 3.12 lub nowszy.")

    from duplicate_finder.cli import main as run_cli

    return run_cli()


if __name__ == "__main__":
    raise SystemExit(main())
