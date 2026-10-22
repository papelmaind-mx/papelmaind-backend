"""Reservation Sweeper — F20: libera reservas blandas a nivel ARTÍCULO.

tarticulos.stock_reservado con TTL 15min (carritos). La verdad dura vive en
tlotes; el hard-allocate FEFO al confirmar pago es el ÚNICO punto que consume
lotes. Verificado por test T12 (canon F20). Sprint 8.
"""
from __future__ import annotations


async def run() -> None:  # pragma: no cover — Sprint 8
    raise NotImplementedError("Reservation sweeper se implementa en Sprint 8 (canon F20)")
