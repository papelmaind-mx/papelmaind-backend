-- Funciones de soporte (canon)
CREATE OR REPLACE FUNCTION set_current_tenant(p_tenant_id UUID)
RETURNS void AS $$
BEGIN
    PERFORM set_config('app.current_tenant_id', p_tenant_id::text, false);
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION set_current_tenant_tx(p_tenant_id UUID)
RETURNS void AS $$
BEGIN
    -- Variante transaccional (SET LOCAL): contexto vigente solo en la TX actual
    PERFORM set_config('app.current_tenant_id', p_tenant_id::text, true);
END;
$$ LANGUAGE plpgsql;
