# Wyszukiwarka zduplikowanych plików

Projekt na przedmiot **Zaawansowane techniki programowania w języku Python**. Aplikacja przeszukuje katalog i jego podkatalogi, wykrywa pliki o tej samej zawartości i zapisuje raport JSON.

## Uruchomienie

Potrzebny jest Python 3.12 lub nowszy. Projekt używa biblioteki standardowej. Uruchom poniższe polecenia w katalogu projektu. Jeśli `python3 --version` pokazuje starszą wersję, użyj w poleceniach nowszego interpretera, np. `python3.13`.

```bash
python3 sample_data/generate_sample_data.py
python3 app.py scan sample_data/generated
```

Wynik demonstracji to 6 przeskanowanych plików, 2 grupy po 2 pliki i 72 B nadmiarowych danych. Raport jest w `reports/duplicates.json`.

| Opcja skanowania | Działanie |
|---|---|
| `--ext txt log` | Wybiera rozszerzenia. Bez tej opcji skan obejmuje wszystkie pliki. |
| `--threads 8` | Ustawia liczbę wątków do obliczania SHA-256. |
| `--batch-size 100` | Ustawia liczbę plików przekazywanych do puli w jednej partii. |
| `--processes 4` | Ustawia liczbę procesów liczących odcisk początku pliku. |
| `--no-processes` | Pomija obliczanie tego odcisku. |
| `--output reports/proba.json` | Zapisuje raport pod wskazaną ścieżką. |

## Jak działa skan

1. Generator przechodzi przez podkatalogi i pomija napotkane dowiązania symboliczne.
2. Skaner grupuje pliki po rozmiarze. Dla grup mających co najmniej dwa pliki pula wątków oblicza SHA-256.
3. Pliki o tym samym rozmiarze i SHA-256 trafiają do jednej grupy. Raport zawiera też informacje z nazw plików, np. datę i oznaczenie `copy` lub `backup`.
4. Pula procesów liczy dodatkowy 32-bitowy odcisk z maksymalnie 256 000 pierwszych bajtów każdego pliku z grupy. Odcisk jest polem raportu. O grupowaniu decyduje SHA-256 wraz z rozmiarem.
5. Raport pokazuje grupy, błędy odczytu i sumę rozmiarów plików nadmiarowych. Sumę wyliczono przy założeniu, że w każdej grupie zostaje jeden plik.

## Wymagania zaliczenia w kodzie

| Zagadnienie | Miejsce i zastosowanie |
|---|---|
| Dekoratory funkcji | W `duplicate_finder/decorators.py` funkcja `measure_time` mierzy czas skanu i benchmarku, a `retry` z parametrami ponawia odczyt w `sha256_file`. Oba dekoratory używają `functools.wraps`. |
| Dekorator metody | W `duplicate_finder/method_decorators.py` funkcja `requires_directory` sprawdza `self.root`. `DuplicateScanner.max_workers` w `scanner.py` używa `@property` z setterem. |
| Iterator | Klasa `FileBatchIterator` w `duplicate_finder/iterators.py` używa `__iter__` i `__next__` do przekazywania partii plików do puli wątków. |
| Generatory | Funkcja `iter_files` w `duplicate_finder/generators.py` używa `yield` i `yield from`. Wyrażenie generujące `candidates` w `scanner.py` wybiera pliki do skrótu. |
| Wyrażenia regularne | W `duplicate_finder/regex_patterns.py` wzorzec `FILENAME_RE` wydobywa nazwę, datę i rozszerzenie, a `COPY_NAME_RE` rozpoznaje oznaczenia kopii. Wzorce używają grup nazwanych. |
| Wątki i synchronizacja | Funkcja `parallel_hash_files` w `duplicate_finder/threading_io.py` używa `ThreadPoolExecutor` i chroni licznik błędów blokadą `Lock`. |
| Procesy | Funkcja `parallel_cpu_fingerprints` w `duplicate_finder/processes_cpu.py` zleca liczenie odcisków w czystym Pythonie przez `ProcessPoolExecutor`. |
| GIL | Funkcja `run_gil_benchmark` w `duplicate_finder/gil_benchmark.py` mierzy czas tego samego obliczenia sekwencyjnie, w wątkach i w procesach. |

## Pomiar GIL

```bash
python3 app.py gil --iterations 20000000 --workers 4
```

Pomiar wykonano na macOS 26.6.2 (ARM64, 10 logicznych CPU), w CPythonie 3.13.16 z włączonym GIL. Każdy tryb liczył cztery zadania po 20 mln iteracji. Czasy są medianami z trzech uruchomień, z uwzględnieniem czasu uruchomienia i zamknięcia puli. Polecenie zapisuje wynik pojedynczego uruchomienia w `reports/gil.json`.

| Tryb | Czas | Przyspieszenie |
|---|---:|---:|
| Sekwencyjnie | 2,316 s | 1,00× |
| 4 wątki | 2,297 s | 1,01× |
| 4 procesy | 0,691 s | 3,35× |

Wątki uzyskały czas zbliżony do wykonania sekwencyjnego. Przy włączonym GIL w jednym procesie tylko jeden wątek naraz wykonuje kod bajtowy Pythona. Procesy mają osobne interpretery i mogą pracować na kilku rdzeniach. W tym pomiarze cztery procesy były 3,35 razy szybsze od wykonania sekwencyjnego. Przy krótszych zadaniach koszt uruchomienia puli może pochłonąć zysk. W skanerze wątki mogą nakładać na siebie operacje odczytu, a `hashlib` zwalnia GIL podczas przetwarzania dużych bloków.

## Problemy podczas realizacji

- Błąd odczytu jednego pliku w puli procesów przerywał skan. Obsługa błędu przy pojedynczym zadaniu pozwala zapisać pozostałe wyniki.
- Przy małej liczbie iteracji koszt uruchomienia puli przesłaniał wpływ GIL. W pomiarze użyto dłuższych zadań i trzech powtórzeń.

## Testy

```bash
python3 -m unittest -v
```
