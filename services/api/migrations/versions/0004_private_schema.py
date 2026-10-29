"""Protect SCOS tables from Supabase browser roles; server access remains through the API."""

from alembic import op
from sqlalchemy import text

revision = "scos_0004"
down_revision = "scos_0003"


def upgrade():
    c = op.get_bind()
    schema = c.execute(text("SELECT current_schema()")).scalar_one()
    if schema == "public":
        return
    q = c.dialect.identifier_preparer.quote
    for (table,) in c.execute(text("SELECT tablename FROM pg_tables WHERE schemaname=:schema"), {"schema": schema}):
        c.exec_driver_sql(f"ALTER TABLE {q(schema)}.{q(table)} ENABLE ROW LEVEL SECURITY")
    for role in ("anon", "authenticated", "PUBLIC"):
        if (
            role != "PUBLIC"
            and not c.execute(text("SELECT 1 FROM pg_roles WHERE rolname=:role"), {"role": role}).first()
        ):
            continue
        c.exec_driver_sql(f"REVOKE ALL ON SCHEMA {q(schema)} FROM {q(role) if role != 'PUBLIC' else role}")
        c.exec_driver_sql(
            f"REVOKE ALL ON ALL TABLES IN SCHEMA {q(schema)} FROM {q(role) if role != 'PUBLIC' else role}"
        )
        c.exec_driver_sql(
            f"REVOKE ALL ON ALL SEQUENCES IN SCHEMA {q(schema)} FROM {q(role) if role != 'PUBLIC' else role}"
        )


def downgrade():
    raise RuntimeError("Security migration downgrade is disabled")
