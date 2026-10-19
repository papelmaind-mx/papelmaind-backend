"""S1: identidad global + multi-tenant + RLS + funciones base (canon v2.2.2).

10 tablas: papelerias, sucursales, currencies, lenguajes,
papeleria_configuracion, tusuarios, usuario_papeleria_rel,
usuario_sesiones, usuario_verificaciones, tauditlogs.
RLS FORCE+WITH CHECK en las 6 tablas con papeleria_id.
"""
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from alembic import op

revision = "0001_s1"
down_revision = None

TENANT_TABLES = [
    "sucursales", "papeleria_configuracion", "usuario_papeleria_rel",
    "usuario_sesiones", "usuario_verificaciones", "tauditlogs",
]


def upgrade() -> None:
    # ── EXTENSIONES ──
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')

    # ── ROLES DB (canon Sección 2, idempotentes) ──
    op.execute("""
    DO $$ BEGIN
        IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname='erp_app') THEN
            CREATE ROLE erp_app LOGIN PASSWORD 'erp_app_dev' NOSUPERUSER NOBYPASSRLS;
        END IF;
        IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname='erp_worker') THEN
            CREATE ROLE erp_worker LOGIN PASSWORD 'erp_worker_dev' NOSUPERUSER BYPASSRLS;
        END IF;
        IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname='erp_migrations') THEN
            CREATE ROLE erp_migrations LOGIN PASSWORD 'erp_mig_dev' NOSUPERUSER;
        END IF;
    END $$;
    """)

    # ── FUNCIONES BASE (canon verbatim) ──
    op.execute("""
    CREATE OR REPLACE FUNCTION generate_uuid_v7() RETURNS uuid AS $$     DECLARE
        v_time timestamptz := clock_timestamp();
        v_secs bigint := EXTRACT(EPOCH FROM v_time)::bigint;
        v_msec bigint := (v_secs * 1000) + (EXTRACT(MILLISECONDS FROM v_time)::bigint % 1000);
        v_buf bytea;
    BEGIN
        v_buf := decode(lpad(to_hex(v_msec), 12, '0') || encode(gen_random_bytes(10), 'hex'), 'hex');
        v_buf := set_byte(v_buf, 6, (get_byte(v_buf, 6) & 15) | 112);
        v_buf := set_byte(v_buf, 8, (get_byte(v_buf, 8) & 63) | 128);
        RETURN encode(v_buf, 'hex')::uuid;
    END; $$ LANGUAGE plpgsql VOLATILE;
    """)

    op.execute("""
    CREATE OR REPLACE FUNCTION set_current_tenant(p UUID) RETURNS void AS $$     BEGIN
        PERFORM set_config('app.current_tenant_id', p::text, true);
    END; $$ LANGUAGE plpgsql SECURITY DEFINER;
    """)

    op.execute("""
    CREATE OR REPLACE FUNCTION fn_set_updated_at() RETURNS TRIGGER AS $$     BEGIN
        NEW.updated_at = NOW();
        RETURN NEW;
    END; $$ LANGUAGE plpgsql;
    """)

    op.execute("""
    CREATE OR REPLACE FUNCTION fn_default_tenant() RETURNS TRIGGER AS $$     BEGIN
        IF NEW.papeleria_id IS NULL THEN
            NEW.papeleria_id := NULLIF(current_setting('app.current_tenant_id', true), '')::uuid;
        END IF;
        RETURN NEW;
    END; $$ LANGUAGE plpgsql;
    """)

    # ── TABLAS GLOBALES (sin RLS: catálogos base / master tenant) ──
    op.create_table("currencies",
        sa.Column("codigo", sa.String(3), primary_key=True),
        sa.Column("nombre", sa.String(50), nullable=False),
        sa.Column("simbolo", sa.String(5), nullable=False),
        sa.Column("tipo_cambio_a_mxn", sa.Numeric(12, 6), nullable=False, server_default=sa.text("1.000000")),
        sa.Column("activa", sa.Boolean, nullable=False, server_default=sa.text("true")),
    )

    op.create_table("lenguajes",
        sa.Column("codigo", sa.String(5), primary_key=True),
        sa.Column("nombre", sa.String(50), nullable=False),
        sa.Column("nombre_nativo", sa.String(50), nullable=False),
        sa.Column("direccion", sa.String(3), nullable=False, server_default=sa.text("'ltr'")),
        sa.Column("activo", sa.Boolean, nullable=False, server_default=sa.text("true")),
    )

    op.create_table("papelerias",
        sa.Column("id", PG_UUID, primary_key=True, server_default=sa.text("generate_uuid_v7()")),
        sa.Column("nombre", sa.String(150), nullable=False),
        sa.Column("slug", sa.String(50), nullable=False, unique=True),
        sa.Column("rfc_emisor", sa.String(15), nullable=True),
        sa.Column("razon_social", sa.String(200), nullable=True),
        sa.Column("plan", sa.String(30), nullable=False, server_default=sa.text("'free'")),
        sa.Column("activa", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
    )
    op.execute("CREATE TRIGGER trg_papelerias_upd BEFORE UPDATE ON papelerias FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at()")

    op.create_table("tusuarios",
        sa.Column("id", PG_UUID, primary_key=True, server_default=sa.text("generate_uuid_v7()")),
        sa.Column("phone_number", sa.String(20), unique=True),
        sa.Column("username", sa.String(50), unique=True),
        sa.Column("display_name", sa.String(100), nullable=False),
        sa.Column("email", sa.Text, unique=True, nullable=True),
        sa.Column("password_hash", sa.Text, nullable=True),
        sa.Column("pin_hash", sa.Text, nullable=True),
        sa.Column("verificado", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("two_factor_secret", sa.Text, nullable=True),
        sa.Column("two_factor_enabled", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("es_bot", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("activo", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("ultimo_acceso", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
    )
    op.execute("CREATE TRIGGER trg_tusuarios_upd BEFORE UPDATE ON tusuarios FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at()")

    # ── TABLAS CON TENANT (RLS abajo) ──
    op.create_table("sucursales",
        sa.Column("id", PG_UUID, primary_key=True, server_default=sa.text("generate_uuid_v7()")),
        sa.Column("papeleria_id", PG_UUID, nullable=False),
        sa.ForeignKeyConstraint(["papeleria_id"], ["papelerias.id"], ondelete="CASCADE"),
        sa.Column("nombre", sa.String(100), nullable=False),
        sa.Column("codigo", sa.String(20), nullable=False),
        sa.Column("direccion", sa.Text, nullable=True),
        sa.Column("telefono", sa.String(20), nullable=True),
        sa.Column("es_default", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("activa", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
    )
    op.execute("CREATE UNIQUE INDEX uq_sucursales_tenant_codigo ON sucursales (papeleria_id, codigo)")
    op.execute("CREATE TRIGGER trg_default_tenant_sucursales BEFORE INSERT ON sucursales FOR EACH ROW EXECUTE FUNCTION fn_default_tenant()")

    op.create_table("papeleria_configuracion",
        sa.Column("id", PG_UUID, primary_key=True, server_default=sa.text("generate_uuid_v7()")),
        sa.Column("papeleria_id", PG_UUID, nullable=False),
        sa.ForeignKeyConstraint(["papeleria_id"], ["papelerias.id"], ondelete="CASCADE"),
        sa.Column("clave", sa.String(100), nullable=False),
        sa.Column("valor", sa.Text, nullable=False),
        sa.Column("descripcion", sa.Text, nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
    )
    op.execute("CREATE UNIQUE INDEX uq_config_tenant_clave ON papeleria_configuracion (papeleria_id, clave)")
    op.execute("CREATE TRIGGER trg_config_upd BEFORE UPDATE ON papeleria_configuracion FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at()")
    op.execute("CREATE TRIGGER trg_default_tenant_config BEFORE INSERT ON papeleria_configuracion FOR EACH ROW EXECUTE FUNCTION fn_default_tenant()")

    op.create_table("usuario_papeleria_rel",
        sa.Column("id", PG_UUID, primary_key=True, server_default=sa.text("generate_uuid_v7()")),
        sa.Column("usuario_id", PG_UUID, nullable=False),
        sa.ForeignKeyConstraint(["usuario_id"], ["tusuarios.id"], ondelete="CASCADE"),
        sa.Column("papeleria_id", PG_UUID, nullable=False),
        sa.ForeignKeyConstraint(["papeleria_id"], ["papelerias.id"], ondelete="CASCADE"),
        sa.Column("rol", sa.String(20), nullable=False),
        sa.Column("saldo_credito", sa.Numeric(12, 2), server_default=sa.text("0")),
        sa.Column("limite_credito", sa.Numeric(12, 2), server_default=sa.text("0")),
        sa.Column("nivel_cliente", sa.String(20), server_default=sa.text("'bronce'")),
        sa.Column("total_compras", sa.Numeric(12, 2), server_default=sa.text("0")),
        sa.Column("num_compras", sa.Integer, server_default=sa.text("0")),
        sa.Column("activo", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
    )
    op.execute("CREATE UNIQUE INDEX uq_rel_usuario_tenant ON usuario_papeleria_rel (usuario_id, papeleria_id)")
    op.execute("CREATE TRIGGER trg_rel_upd BEFORE UPDATE ON usuario_papeleria_rel FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at()")
    op.execute("CREATE TRIGGER trg_default_tenant_rel BEFORE INSERT ON usuario_papeleria_rel FOR EACH ROW EXECUTE FUNCTION fn_default_tenant()")

    op.create_table("usuario_sesiones",
        sa.Column("id", PG_UUID, primary_key=True, server_default=sa.text("generate_uuid_v7()")),
        sa.Column("papeleria_id", PG_UUID, nullable=False),
        sa.ForeignKeyConstraint(["papeleria_id"], ["papelerias.id"], ondelete="CASCADE"),
        sa.Column("usuario_id", PG_UUID, nullable=False),
        sa.ForeignKeyConstraint(["usuario_id"], ["tusuarios.id"], ondelete="CASCADE"),
        sa.Column("refresh_token_hash", sa.String(255), nullable=False, unique=True),
        sa.Column("dispositivo", sa.Text, nullable=True),
        sa.Column("ip_address", sa.dialects.postgresql.INET, nullable=True),
        sa.Column("user_agent", sa.Text, nullable=True),
        sa.Column("activa", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
    )
    op.execute("CREATE INDEX idx_sesiones_expiracion ON usuario_sesiones (expires_at) WHERE activa = true")

    op.create_table("usuario_verificaciones",
        sa.Column("id", PG_UUID, primary_key=True, server_default=sa.text("generate_uuid_v7()")),
        sa.Column("papeleria_id", PG_UUID, nullable=False),
        sa.ForeignKeyConstraint(["papeleria_id"], ["papelerias.id"], ondelete="CASCADE"),
        sa.Column("usuario_id", PG_UUID, nullable=False),
        sa.ForeignKeyConstraint(["usuario_id"], ["tusuarios.id"], ondelete="CASCADE"),
        sa.Column("canal", sa.String(10), nullable=False),
        sa.Column("token_hash", sa.String(255), nullable=False),
        sa.Column("tipo", sa.String(20), nullable=False),
        sa.Column("expira_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("intentos", sa.Integer, server_default=sa.text("0")),
        sa.Column("consumido", sa.Boolean, nullable=False, server_default=sa.text("false")),
    )

    op.create_table("tauditlogs",
        sa.Column("id", PG_UUID, primary_key=True, server_default=sa.text("generate_uuid_v7()")),
        sa.Column("papeleria_id", PG_UUID, nullable=True),
        sa.Column("usuario_id", PG_UUID, nullable=True),
        sa.Column("tabla_afectada", sa.Text, nullable=False),
        sa.Column("registro_id", PG_UUID, nullable=False),
        sa.Column("accion", sa.String(30), nullable=False),
        sa.Column("datos_anteriores", sa.dialects.postgresql.JSONB, nullable=True),
        sa.Column("datos_nuevos", sa.dialects.postgresql.JSONB, nullable=True),
        sa.Column("trace_id", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
    )

    # ── RLS: FORCE + WITH CHECK en las 6 tablas tenant (canon) ──
    for tabla in TENANT_TABLES:
        op.execute(f"ALTER TABLE {tabla} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {tabla} FORCE ROW LEVEL SECURITY")
        op.execute(f"""
        CREATE POLICY tenant_isolation_{tabla} ON {tabla} FOR ALL
        USING (papeleria_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
        WITH CHECK (papeleria_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
        """)

    # ── GRANTS (canon Sección 2) ──
    op.execute("GRANT USAGE ON SCHEMA public TO erp_app, erp_worker, erp_migrations")
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO erp_app, erp_worker")
    op.execute("GRANT ALL ON SCHEMA public TO erp_migrations")
    op.execute("REVOKE ALL ON SCHEMA public FROM PUBLIC")


def downgrade() -> None:
    for tabla in reversed(TENANT_TABLES):
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation_{tabla} ON {tabla}")
    op.execute("DROP TABLE IF EXISTS tauditlogs, usuario_verificaciones, usuario_sesiones, usuario_papeleria_rel, papeleria_configuracion, sucursales, tusuarios, papelerias, lenguajes, currencies CASCADE")
    op.execute("DROP FUNCTION IF EXISTS fn_default_tenant(), fn_set_updated_at(), set_current_tenant(uuid), generate_uuid_v7()")
