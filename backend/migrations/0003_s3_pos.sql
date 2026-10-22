-- ============================================================
-- PapelMaind — 0003_s3_pos.sql (Sprint 3: POS transaccional)
-- Ventas + detalles + pagos + historial + outbox F17 + DLQ
-- Nota: tcortescaja llega en S4 → corte_id sin FK aún (nullable)
-- ============================================================

CREATE TABLE IF NOT EXISTS tventas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    papeleria_id UUID NOT NULL REFERENCES papelerias(id),
    sucursal_id UUID REFERENCES sucursales(id),
    estacion_id UUID REFERENCES estaciones(id),
    cliente_rel_id UUID REFERENCES usuario_papeleria_rel(id),
    corte_id UUID,  -- FK a tcortescaja en migración S4
    folio VARCHAR(30),
    client_uuid UUID NOT NULL UNIQUE,  -- CONV-13: idempotencia offline-first
    subtotal NUMERIC(12,2) NOT NULL DEFAULT 0,
    impuestos NUMERIC(12,2) NOT NULL DEFAULT 0,
    total NUMERIC(12,2) NOT NULL DEFAULT 0,
    metodo_pago TEXT
        CHECK (metodo_pago IN ('efectivo','tarjeta','transferencia','spei','mixto','credito','puntos')),
    estado TEXT NOT NULL DEFAULT 'completada',
    origen TEXT CHECK (origen IN ('pos','rompefila','ecommerce','whatsapp','kiosco')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS tdetallesventa (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    papeleria_id UUID NOT NULL REFERENCES papelerias(id),
    venta_id UUID NOT NULL REFERENCES tventas(id),
    articulo_id UUID NOT NULL REFERENCES tarticulos(id),
    lote_id UUID REFERENCES tlotes(id),
    cantidad NUMERIC(12,3) NOT NULL,
    precio_unitario NUMERIC(12,2) NOT NULL,
    subtotal NUMERIC(12,2) NOT NULL,
    impuesto_id UUID REFERENCES timpuestos(id)
);

CREATE TABLE IF NOT EXISTS tpagosventa (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    papeleria_id UUID NOT NULL REFERENCES papelerias(id),
    venta_id UUID NOT NULL REFERENCES tventas(id),
    tipo TEXT NOT NULL
        CHECK (tipo IN ('efectivo','tarjeta','transferencia','puntos','credito')),
    monto NUMERIC(12,2) NOT NULL
);

CREATE TABLE IF NOT EXISTS thistorialventas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    venta_id UUID NOT NULL REFERENCES tventas(id),
    estado_anterior TEXT,
    estado_nuevo TEXT NOT NULL,
    motivo TEXT
);

-- ---------- Outbox F17: flags SEPARADOS por consumidor ----------
CREATE TABLE IF NOT EXISTS outbox_eventos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    papeleria_id UUID NOT NULL REFERENCES papelerias(id),
    tipo TEXT NOT NULL,
    aggregate_type VARCHAR(50),
    aggregate_id VARCHAR(100),
    payload JSONB NOT NULL,
    client_uuid UUID UNIQUE,
    publicado_kafka BOOLEAN NOT NULL DEFAULT FALSE,
    procesado_loyalty BOOLEAN NOT NULL DEFAULT FALSE,
    intentos INT NOT NULL DEFAULT 0,
    error_ultimo TEXT,
    procesado_en TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_outbox_loyalty_p0
    ON outbox_eventos (created_at)
    WHERE tipo = 'sale.completed' AND procesado_loyalty = FALSE;
CREATE INDEX IF NOT EXISTS idx_outbox_kafka_p1
    ON outbox_eventos (created_at)
    WHERE publicado_kafka = FALSE AND intentos < 3;

-- ---------- DLQ (errores de dominio terminales) ----------
CREATE TABLE IF NOT EXISTS tdlq_eventos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    outbox_evento_id UUID NOT NULL UNIQUE,
    papeleria_id UUID REFERENCES papelerias(id),
    event_type TEXT,
    aggregate_type VARCHAR(50),
    aggregate_id VARCHAR(100),
    payload JSONB,
    error_ultimo TEXT,
    historial_intentos JSONB NOT NULL DEFAULT '[]',
    trace_id VARCHAR(64),
    estado TEXT NOT NULL DEFAULT 'pendiente'
        CHECK (estado IN ('pendiente','reintentado','descartado','resuelto')),
    motivo_descarte TEXT,
    descartado_por UUID REFERENCES tusuarios(id),
    descartado_en TIMESTAMPTZ,
    replayer_corrida_id UUID,
    first_failed_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_dlq_pendientes
    ON tdlq_eventos (first_failed_at)
    WHERE estado = 'pendiente';

CREATE INDEX IF NOT EXISTS ix_ventas_tenant ON tventas(papeleria_id);
CREATE INDEX IF NOT EXISTS ix_ventas_created ON tventas(papeleria_id, created_at DESC);
CREATE INDEX IF NOT EXISTS ix_detalles_venta ON tdetallesventa(venta_id);
CREATE INDEX IF NOT EXISTS ix_pagos_venta ON tpagosventa(venta_id);
CREATE INDEX IF NOT EXISTS ix_historial_venta ON thistorialventas(venta_id);

-- ---------- RLS (tenant_isolation) ----------
ALTER TABLE tventas ENABLE ROW LEVEL SECURITY;
ALTER TABLE tventas FORCE ROW LEVEL SECURITY;
ALTER TABLE tdetallesventa ENABLE ROW LEVEL SECURITY;
ALTER TABLE tdetallesventa FORCE ROW LEVEL SECURITY;
ALTER TABLE tpagosventa ENABLE ROW LEVEL SECURITY;
ALTER TABLE tpagosventa FORCE ROW LEVEL SECURITY;
ALTER TABLE thistorialventas ENABLE ROW LEVEL SECURITY;
ALTER TABLE thistorialventas FORCE ROW LEVEL SECURITY;
ALTER TABLE outbox_eventos ENABLE ROW LEVEL SECURITY;
ALTER TABLE outbox_eventos FORCE ROW LEVEL SECURITY;
ALTER TABLE tdlq_eventos ENABLE ROW LEVEL SECURITY;
ALTER TABLE tdlq_eventos FORCE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation_tventas ON tventas
    USING (papeleria_id = current_setting('app.current_tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_tdetallesventa ON tdetallesventa
    USING (papeleria_id = current_setting('app.current_tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_tpagosventa ON tpagosventa
    USING (papeleria_id = current_setting('app.current_tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_outbox ON outbox_eventos
    USING (papeleria_id = current_setting('app.current_tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_tdlq ON tdlq_eventos
    USING (papeleria_id = current_setting('app.current_tenant_id', true)::uuid);

-- Rol worker: BYPASSRLS explícito para los 9 workers (CONV-07)
GRANT SELECT, INSERT, UPDATE ON tventas, tdetallesventa, tpagosventa,
    thistorialventas, outbox_eventos, tdlq_eventos TO erp_worker;
