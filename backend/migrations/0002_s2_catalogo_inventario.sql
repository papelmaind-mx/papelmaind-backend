-- ============================================================
-- PapelMaind — 0002_s2_catalogo_inventario.sql (Sprint 2)
-- Catálogo por tenant (CONV-17) + lotes + movimientos + RLS
-- ============================================================

CREATE TABLE IF NOT EXISTS tunidadesmedida (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    papeleria_id UUID NOT NULL REFERENCES papelerias(id),
    clave VARCHAR(10) NOT NULL,
    nombre VARCHAR(50) NOT NULL,
    permite_decimales BOOLEAN NOT NULL DEFAULT FALSE,
    CONSTRAINT uq_um_tenant_clave UNIQUE (papeleria_id, clave)
);

CREATE TABLE IF NOT EXISTS timpuestos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    papeleria_id UUID NOT NULL REFERENCES papelerias(id),
    nombre VARCHAR(50) NOT NULL,
    tipo TEXT NOT NULL CHECK (tipo IN ('iva','ieps','exento')),
    tasa NUMERIC(5,4) NOT NULL
);

CREATE TABLE IF NOT EXISTS tarticulos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    papeleria_id UUID NOT NULL REFERENCES papelerias(id),
    sku VARCHAR(50) NOT NULL,
    descripcion TEXT NOT NULL,
    specs JSONB NOT NULL DEFAULT '{}',
    unidad_medida_id UUID NOT NULL REFERENCES tunidadesmedida(id),
    impuesto_id UUID REFERENCES timpuestos(id),
    precio_base NUMERIC(12,4) NOT NULL DEFAULT 0,
    activo_web BOOLEAN NOT NULL DEFAULT TRUE,
    stock_actual NUMERIC(12,3) NOT NULL DEFAULT 0,
    stock_reservado NUMERIC(12,3) NOT NULL DEFAULT 0,
    stock_minimo NUMERIC(12,3) NOT NULL DEFAULT 10,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_articulo_tenant_sku UNIQUE (papeleria_id, sku)
);

CREATE TABLE IF NOT EXISTS tlotes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    papeleria_id UUID NOT NULL REFERENCES papelerias(id),
    sucursal_id UUID REFERENCES sucursales(id),
    articulo_id UUID NOT NULL REFERENCES tarticulos(id),
    numero_lote VARCHAR(50) NOT NULL,
    fecha_vencimiento DATE NOT NULL,
    costo_unitario NUMERIC(12,4) NOT NULL DEFAULT 0,
    cantidad_actual NUMERIC(12,3) NOT NULL,
    cantidad_reservada NUMERIC(12,3) NOT NULL DEFAULT 0,
    estado TEXT NOT NULL DEFAULT 'disponible'
        CHECK (estado IN ('disponible','parcial','agotado','vencido','devuelto')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_lote_tenant_numero UNIQUE (papeleria_id, numero_lote)
);

CREATE TABLE IF NOT EXISTS tmovinventario (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    papeleria_id UUID NOT NULL REFERENCES papelerias(id),
    sucursal_id UUID REFERENCES sucursales(id),
    articulo_id UUID NOT NULL REFERENCES tarticulos(id),
    lote_id UUID REFERENCES tlotes(id),
    tipo_movimiento TEXT NOT NULL CHECK (tipo_movimiento IN ('entrada','salida','ajuste','reserva','liberacion','transferencia')),
    cantidad NUMERIC(12,3) NOT NULL,
    motivo TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_articulos_tenant ON tarticulos(papeleria_id);
CREATE INDEX IF NOT EXISTS ix_articulos_sku ON tarticulos(papeleria_id, sku);
CREATE INDEX IF NOT EXISTS ix_lotes_articulo ON tlotes(articulo_id);
CREATE INDEX IF NOT EXISTS ix_lotes_vencimiento ON tlotes(papeleria_id, articulo_id, fecha_vencimiento);
CREATE INDEX IF NOT EXISTS ix_mov_articulo ON tmovinventario(articulo_id);

-- ---------- RLS (S2) — T5 rls_disjoint ----------
ALTER TABLE tunidadesmedida ENABLE ROW LEVEL SECURITY;
ALTER TABLE timpuestos ENABLE ROW LEVEL SECURITY;
ALTER TABLE tarticulos ENABLE ROW LEVEL SECURITY;
ALTER TABLE tlotes ENABLE ROW LEVEL SECURITY;
ALTER TABLE tmovinventario ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation_um ON tunidadesmedida
    USING (papeleria_id = current_setting('app.current_tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_imp ON timpuestos
    USING (papeleria_id = current_setting('app.current_tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_articulos ON tarticulos
    USING (papeleria_id = current_setting('app.current_tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_lotes ON tlotes
    USING (papeleria_id = current_setting('app.current_tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_mov ON tmovinventario
    USING (papeleria_id = current_setting('app.current_tenant_id', true)::uuid);

-- Vista de stock por sucursal (canon: fuente de verdad = tlotes)
CREATE OR REPLACE VIEW vw_stock_sucursal AS
SELECT l.papeleria_id, l.sucursal_id, l.articulo_id,
       SUM(l.cantidad_actual - l.cantidad_reservada) AS disponible
FROM tlotes l
WHERE l.estado NOT IN ('vencido','devuelto')
GROUP BY 1, 2, 3;
