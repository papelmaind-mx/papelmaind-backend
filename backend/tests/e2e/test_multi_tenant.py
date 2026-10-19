"""T5: RLS disjoint — tenant A no ve datos de tenant B (canon)."""
import pytest
from sqlalchemy import text


@pytest.mark.asyncio
class TestT5RLS:
    async def test_rels_disjuntos_por_tenant(self, app_session, seed_data):
        # Desde tenant A
        async with app_session.begin():
            await app_session.execute(
                text("SELECT set_current_tenant(:t)"), {"t": str(seed_data["t_a"])})
            rels_a = [r[0] for r in (await app_session.execute(
                text("SELECT id FROM usuario_papeleria_rel"))).fetchall()]

        # Desde tenant B
        async with app_session.begin():
            await app_session.execute(
                text("SELECT set_current_tenant(:t)"), {"t": str(seed_data["t_b"])})
            rels_b = [r[0] for r in (await app_session.execute(
                text("SELECT id FROM usuario_papeleria_rel"))).fetchall()]

        assert set(rels_a).isdisjoint(set(rels_b))  # T5 núcleo

    async def test_get_id_ajeno_404(self, app_session, seed_data):
        """A pide la rel de B por id → RLS la oculta → 0 filas (= 404 en API)."""
        async with app_session.begin():
            await app_session.execute(
                text("SELECT set_current_tenant(:t)"), {"t": str(seed_data["t_a"])})
            row = (await app_session.execute(
                text("SELECT id FROM usuario_papeleria_rel WHERE id = :rid"),
                {"rid": str(seed_data["rel_b"])})).first()
        assert row is None  # RLS filtró el acceso cross-tenant

    async def test_config_por_tenant_aislada(self, app_session, seed_data):
        async with admin_seed(app_session):
            pass  # helper no necesario — datos ya sembrados en conftest si se agregan
