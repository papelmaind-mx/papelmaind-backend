"""T5 — RLS isolation entre papelerías."""
import pytest

@pytest.mark.asyncio
async def test_rls_isolation_between_tenants():
    """Usuario de papelería A no ve filas de papelería B."""
    pytest.skip("Implementar en Sprint 1")
