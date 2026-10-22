"""Inventory Alert Worker — F18: reposiciones desde talertasreposicion.

Evalúa stock_actual vs stock_minimo (o dinámico demanda30d × lead_time × 1.5)
y genera alertas de reposición. Sprint 6.
"""
from __future__ import annotations


async def run() -> None:  # pragma: no cover — Sprint 6
    raise NotImplementedError("Inventory alert worker se implementa en Sprint 6 (canon F18)")
