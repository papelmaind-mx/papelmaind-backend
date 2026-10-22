-- ============================================================
-- PapelMaind — 0001_s1_fundacion.sql (Sprint 1)
-- PostgreSQL 16 · RLS multi-tenant · tablas en español (CONV-02)
-- NOTA: en dev sin Docker el schema se crea desde SQLAlchemy metadata
--       (SQLite, RLS emulado). Este archivo es la fuente para producción.
-- ============================================================

CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ---------- Tenancy ----------
CREATE TABLE IF NOT EXISTS papelerias (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nombre VARCHAR(150) NOT NULL,
    slug VARCHAR(50) NOT NULL,
    plan VARCHAR(30) NOT NULL DEFAULT 'free',
    activa BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT uq_papeleria_slug UNIQUE (slug)
);

CREATE TABLE IF NOT EXISTS sucursales (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    papeleria_id UUID NOT NULL REFERENCES papelerias(id),
    nombre VARCHAR(100) NOT NULL,
    codigo VARCHAR(20) NOT NULL,
    CONSTRAINT uq_sucursal_codigo UNIQUE (papeleria_id, codigo)
);

CREATE TABLE IF NOT EXISTS cajas_registradoras (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    papeleria_id UUID NOT NULL REFERENCES papelerias(id),
    sucursal_id UUID NOT NULL REFERENCES sucursales(id),
    codigo VARCHAR(20) NOT NULL,
    tipo TEXT NOT NULL DEFAULT 'fisica',
    fondo_fijo_default NUMERIC(12,2) DEFAULT 0
);

CREATE TABLE IF NOT EXISTS estaciones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    papeleria_id UUID NOT NULL REFERENCES papelerias(id),
    sucursal_id UUID NOT NULL REFERENCES sucursales(id),
    codigo VARCHAR(3) NOT NULL,
    -- F26: MAYÚSCULAS — identificador de terminal, no estado de dominio
    tipo TEXT NOT NULL CHECK (tipo IN ('POS','WEB','MOVIL','API','KIOSCO','EMPAQUE')),
    caja_id UUID REFERENCES cajas_registradoras(id)
);

-- ---------- Usuarios ----------
CREATE TABLE IF NOT EXISTS tusuarios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone_number VARCHAR(20) UNIQUE,
    username VARCHAR(50) NOT NULL UNIQUE,
    display_name VARCHAR(100),
    password_hash TEXT,
    pin_hash TEXT,
    two_factor_secret TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS usuario_papeleria_rel (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id UUID NOT NULL REFERENCES tusuarios(id),
    papeleria_id UUID NOT NULL REFERENCES papelerias(id),
    rol VARCHAR(20) NOT NULL CHECK (rol IN ('superadmin','admin','cajero','contador','cliente','system','repartidor','proveedor')),
    nivel_cliente VARCHAR(20) NOT NULL DEFAULT 'bronce' CHECK (nivel_cliente IN ('bronce','plata','oro','diamante')),
    CONSTRAINT uq_usuario_papeleria UNIQUE (usuario_id, papeleria_id)
);

CREATE TABLE IF NOT EXISTS usuario_sesiones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id UUID NOT NULL REFERENCES tusuarios(id),
    papeleria_id UUID,
    refresh_token_hash VARCHAR(255) NOT NULL UNIQUE,
    expires_at TIMESTAMPTZ NOT NULL,
    revoked_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_rel_usuario ON usuario_papeleria_rel(usuario_id);
CREATE INDEX IF NOT EXISTS ix_rel_papeleria ON usuario_papeleria_rel(papeleria_id);

-- ---------- RLS (S1) ----------
ALTER TABLE sucursales ENABLE ROW LEVEL SECURITY;
ALTER TABLE cajas_registradoras ENABLE ROW LEVEL SECURITY;
ALTER TABLE estaciones ENABLE ROW LEVEL SECURITY;
ALTER TABLE usuario_papeleria_rel ENABLE ROW LEVEL SECURITY;
ALTER TABLE usuario_sesiones ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation_sucursales ON sucursales
    USING (papeleria_id = current_setting('app.current_tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_cajas ON cajas_registradoras
    USING (papeleria_id = current_setting('app.current_tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_estaciones ON estaciones
    USING (papeleria_id = current_setting('app.current_tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_rel ON usuario_papeleria_rel
    USING (papeleria_id = current_setting('app.current_tenant_id', true)::uuid
           OR usuario_id = current_setting('app.current_user_id', true)::uuid);
