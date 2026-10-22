-- Suite RLS (canon Sección 2): garantiza RLS activo en TODA tabla con papeleria_id.
-- Las políticas específicas viven en backend/migrations/000{1,2}_*.sql
DO $$
DECLARE
    t TEXT;
BEGIN
    FOR t IN
        SELECT c.table_name
        FROM information_schema.columns c
        JOIN information_schema.tables tb
          ON tb.table_schema = c.table_schema AND tb.table_name = c.table_name
        WHERE c.table_schema = 'public'
          AND c.column_name = 'papeleria_id'
          AND tb.table_type = 'BASE TABLE'
    LOOP
        EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY', t);
        IF NOT EXISTS (
            SELECT 1 FROM pg_policies
            WHERE schemaname = 'public' AND tablename = t
              AND policyname = 'tenant_isolation_' || t
        ) THEN
            EXECUTE format(
                'CREATE POLICY %I ON %I USING (papeleria_id = current_setting(''app.current_tenant_id'', true)::uuid)',
                'tenant_isolation_' || t, t
            );
        END IF;
    END LOOP;
END
$$;
