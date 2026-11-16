"""Benchmark wpływu GIL: sekwencyjnie vs wątki vs procesy."""

from __future__ import annotations

import multiprocessing
import os
import sys
import sysconfig
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor

from .decorators import measure_time


def cpu_work(iterations: int) -> int:
    """Czyste obliczenie CPU-bound wykonywane w Pythonie."""
    total = 0
    for i in range(iterations):
        total += (i * i) % 97
    return total


def _measure_sequential(tasks: list[int]) -> float:
    start = time.perf_counter()
    for task in tasks:
        cpu_work(task)
    return time.perf_counter() - start


def _measure_executor(
    executor_cls: type[ThreadPoolExecutor] | type[ProcessPoolExecutor],
    tasks: list[int],
    workers: int,
) -> float:
    start = time.perf_counter()
    executor: ThreadPoolExecutor | ProcessPoolExecutor
    if executor_cls is ProcessPoolExecutor:
        context = multiprocessing.get_context("spawn")
        executor = ProcessPoolExecutor(max_workers=workers, mp_context=context)
    else:
        executor = ThreadPoolExecutor(max_workers=workers)
    with executor:
        list(executor.map(cpu_work, tasks))
    return time.perf_counter() - start


@measure_time
def run_gil_benchmark(
    iterations: int = 2_000_000, workers: int = 4
) -> dict[str, float | int | str | bool]:
    """Mierzy czas wykonania tych samych obliczeń w trzech trybach."""
    if iterations <= 0 or workers <= 0:
        raise ValueError("Liczba iteracji i pracowników musi być dodatnia.")

    tasks = [iterations] * workers
    sequential = _measure_sequential(tasks)
    threads = _measure_executor(ThreadPoolExecutor, tasks, workers)
    processes = _measure_executor(ProcessPoolExecutor, tasks, workers)

    speedup_threads = sequential / threads if threads else 0.0
    speedup_processes = sequential / processes if processes else 0.0

    free_threading_build = bool(sysconfig.get_config_var("Py_GIL_DISABLED"))
    gil_check = getattr(sys, "_is_gil_enabled", None)
    gil_enabled = None
    if gil_check is not None:
        gil_enabled = gil_check()
    elif sys.implementation.name == "cpython" and not free_threading_build:
        gil_enabled = True

    return {
        "python_version": sys.version.split()[0],
        "cpu_count": os.cpu_count() or 1,
        "gil_enabled": str(gil_enabled),
        "sequential_s": sequential,
        "threads_s": threads,
        "processes_s": processes,
        "threads_speedup": speedup_threads,
        "processes_speedup": speedup_processes,
        "iterations_per_task": iterations,
        "workers": workers,
        "free_threading_build": free_threading_build,
    }


def format_benchmark(result: dict[str, float | int | str | bool]) -> str:
    """Formatuje wynik benchmarku do prezentacji na zajęciach."""
    return (
        "\n"
        "=== BENCHMARK GIL ===\n"
        f"Python: {result['python_version']}\n"
        f"Logiczne CPU: {result['cpu_count']}\n"
        f"GIL włączony: {result['gil_enabled']}\n"
        f"Kompilacja free-threading: {result['free_threading_build']}\n"
        f"Iteracje na zadanie: {result['iterations_per_task']}\n"
        f"Liczba zadań i rozmiar puli: {result['workers']}\n"
        f"Sekwencyjnie: {result['sequential_s']:.3f} s\n"
        f"Wątki:       {result['threads_s']:.3f} s (×{result['threads_speedup']:.2f})\n"
        f"Procesy:     {result['processes_s']:.3f} s (×{result['processes_speedup']:.2f})"
    )
