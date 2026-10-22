"""T12 reservation_sweeper ↔ vw_stock_sucursal — F20 (canon estructura tests).

Requiere carritos con reserva blanda TTL 15min (Sprint 8).
"""
from __future__ import annotations

import pytest

pytestmark = [pytest.mark.asyncio, pytest.mark.skip(reason="Sprint 8 — carritos + sweeper")]


async def test_sweeper_libera_reserva_expirada_placeholder() -> None:
    """F20: sweeper libera stock_reservado a nivel artículo tras TTL 15min."""
    assert True
