"""Métricas Prometheus (canon: 24 métricas). Registro mínimo sin dependencia externa.

P0: contadores/histogramas en memoria con exposición text/plain en /metrics.
P1: migración a prometheus_client sin cambiar la interfaz de registro.
"""
from __future__ import annotations

import time
from collections import defaultdict
from collections.abc import Awaitable, Callable
from contextlib import contextmanager
from functools import wraps
from typing import Any, TypeVar

from src.core.config import settings

T = TypeVar("T")

_counters: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
_histograms: dict[str, list[float]] = defaultdict(list)
_gauges: dict[str, float] = {}


def inc_counter(name: str, labels: dict[str, str] | None = None, value: float = 1.0) -> None:
    key = ",".join(f'{k}="{v}"' for k, v in sorted((labels or {}).items()))
    _counters[name][key] += value


def observe_histogram(name: str, value: float, labels: dict[str, str] | None = None) -> None:
    suffix = ",".join(f'{k}="{v}"' for k, v in sorted((labels or {}).items()))
    _histograms[f"{name}|{suffix}"].append(value)


def set_gauge(name: str, value: float) -> None:
    _gauges[name] = value


def render_metrics() -> str:
    lines: list[str] = []
    for name, series in sorted(_counters.items()):
        for labels, value in sorted(series.items()):
            lines.append(f'{name}{{{labels}}} {value:g}')
    for name, value in sorted(_gauges.items()):
        lines.append(f"{name} {value:g}")
    for name, values in sorted(_histograms.items()):
        metric, _, labels = name.partition("|")
        if values:
            ordered = sorted(values)
            p95 = ordered[min(len(ordered) - 1, int(len(ordered) * 0.95))]
            lines.append(f'{metric}_p95{{{labels}}} {p95:.6f}')
            lines.append(f'{metric}_count{{{labels}}} {len(values)}')
    return "\n".join(lines) + "\n"


@contextmanager
def track_latency(metric: str, labels: dict[str, str] | None = None):
    """Context manager: mide latencia de un bloque."""
    t0 = time.perf_counter()
    try:
        yield
    finally:
        observe_histogram(metric, time.perf_counter() - t0, labels)


def monitor_latency(
    metric: str, labels: dict[str, str] | None = None
) -> Callable[[Callable[..., Awaitable[T]]], Callable[..., Awaitable[T]]]:
    """Decorador para funciones async: registra latencia (erp_fefo_allocation_latency_seconds)."""

    def decorator(fn: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @wraps(fn)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            t0 = time.perf_counter()
            try:
                return await fn(*args, **kwargs)
            finally:
                observe_histogram(metric, time.perf_counter() - t0, labels)

        return wrapper

    return decorator


def metrics_enabled() -> bool:
    return settings.app_env in ("development", "production")
