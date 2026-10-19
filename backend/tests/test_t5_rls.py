"""T5 — RLS isolation entre papelerías."""
import pytest

@pytest.mark.asyncio
async def test_rls_isolation_between_tenants():
    """Usuario de papelería A no ve filas de papelería B con set_current_tenant."""
    pytest.skip("Conectar DB de test + políticas RLS en S1")
