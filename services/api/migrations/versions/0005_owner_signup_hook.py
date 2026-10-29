from alembic import op
from sqlalchemy import text

revision = "scos_0005"
down_revision = "scos_0004"


def upgrade():
    c = op.get_bind()
    schema = c.execute(text("SELECT current_schema()")).scalar_one()
    if schema == "public":
        return
    q = c.dialect.identifier_preparer.quote
    s = q(schema)
    c.exec_driver_sql(f"""CREATE TABLE {s}.hosted_owner_policy (
        singleton boolean PRIMARY KEY DEFAULT true CHECK(singleton), owner_email text NOT NULL,
        created_at timestamptz NOT NULL DEFAULT now());
        ALTER TABLE {s}.hosted_owner_policy ENABLE ROW LEVEL SECURITY;""")
    c.exec_driver_sql(f"""CREATE FUNCTION {s}.restrict_signup(event jsonb) RETURNS jsonb
        LANGUAGE plpgsql SECURITY DEFINER SET search_path='' AS $$
        DECLARE allowed text;
        BEGIN
          SELECT owner_email INTO allowed FROM {s}.hosted_owner_policy WHERE singleton=true;
          IF allowed IS NULL OR lower(coalesce(event->'user'->>'email','')) != lower(allowed)
             OR coalesce(event->'user'->'app_metadata'->>'provider','') != 'google' THEN
            RETURN jsonb_build_object('error',jsonb_build_object('http_code',403,'message','Owner Google account required'));
          END IF;
          RETURN '{{}}'::jsonb;
        END; $$;
        REVOKE ALL ON FUNCTION {s}.restrict_signup(jsonb) FROM PUBLIC;""")
    if c.execute(text("SELECT 1 FROM pg_roles WHERE rolname='supabase_auth_admin'")).first():
        c.exec_driver_sql(f"GRANT USAGE ON SCHEMA {s} TO supabase_auth_admin")
        c.exec_driver_sql(f"GRANT EXECUTE ON FUNCTION {s}.restrict_signup(jsonb) TO supabase_auth_admin")


def downgrade():
    raise RuntimeError("Security migration downgrade is disabled")
