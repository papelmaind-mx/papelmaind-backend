-- Roles de aplicación (canon CONV-07: erp_app con RLS · erp_worker BYPASSRLS solo workers)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'erp_app') THEN
        CREATE ROLE erp_app NOLOGIN;
    END IF;
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'erp_worker') THEN
        CREATE ROLE erp_worker NOLOGIN BYPASSRLS;
    END IF;
END
$$;
