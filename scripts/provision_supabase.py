"""Apply the SCOS runtime-role grants after an operator runs the isolated migrations.

Run with the NEW project's migration credential. Never prints a password or URL.
Existing runtime passwords are preserved; rotation is a separate operation.
"""

import os
from psycopg import sql
from scos import config
from scos.db import connect


def main():
    config.validate()
    if config.DATA_PROVIDER != "supabase" or not config.HOSTED or not config.OWNER_EMAIL:
        raise RuntimeError("An isolated hosted Supabase project and owner allowlist are required")
    schema, role = config.DATABASE_SCHEMA, config.DATABASE_SCHEMA + "_app"
    with connect() as c:
        if c.execute("SELECT current_schema() AS name").fetchone()["name"] != schema:
            raise RuntimeError("SCOS_RESOURCE_ISOLATION: wrong schema")
        c.execute(
            "INSERT INTO hosted_owner_policy(singleton,owner_email) VALUES(true,%s) ON CONFLICT(singleton) DO UPDATE SET owner_email=excluded.owner_email",
            (config.OWNER_EMAIL,),
        )
        if not c.execute("SELECT 1 FROM pg_roles WHERE rolname=%s", (role,)).fetchone():
            password = os.getenv("SCOS_RUNTIME_DB_PASSWORD", "")
            if len(password) < 32:
                raise RuntimeError(
                    "Set a new runtime password of at least 32 characters directly in the operator environment"
                )
            c.execute(sql.SQL("CREATE ROLE {} LOGIN PASSWORD {}").format(sql.Identifier(role), sql.Literal(password)))
        c.execute(sql.SQL("GRANT USAGE ON SCHEMA {} TO {}").format(sql.Identifier(schema), sql.Identifier(role)))
        for table in c.execute("SELECT tablename FROM pg_tables WHERE schemaname=%s", (schema,)).fetchall():
            name = table["tablename"]
            target = sql.Identifier(schema, name)
            c.execute(sql.SQL("ALTER TABLE {} ENABLE ROW LEVEL SECURITY").format(target))
            if name == "hosted_owner_policy":
                c.execute(sql.SQL("REVOKE ALL ON {} FROM {}").format(target, sql.Identifier(role)))
                continue
            privileges = sql.SQL("SELECT") if name == "alembic_version" else sql.SQL("SELECT,INSERT,UPDATE,DELETE")
            if name == "alembic_version":
                c.execute(sql.SQL("REVOKE INSERT,UPDATE,DELETE ON {} FROM {}").format(target, sql.Identifier(role)))
            c.execute(sql.SQL("GRANT {} ON {} TO {}").format(privileges, target, sql.Identifier(role)))
            exists = c.execute(
                "SELECT 1 FROM pg_policies WHERE schemaname=%s AND tablename=%s AND policyname='scos_server_access'",
                (schema, name),
            ).fetchone()
            if not exists:
                c.execute(
                    sql.SQL("CREATE POLICY scos_server_access ON {} FOR ALL TO {} USING(true) WITH CHECK(true)").format(
                        target, sql.Identifier(role)
                    )
                )
        c.execute(
            sql.SQL("GRANT USAGE,SELECT ON ALL SEQUENCES IN SCHEMA {} TO {}").format(
                sql.Identifier(schema), sql.Identifier(role)
            )
        )
    print("Isolated Supabase runtime grants and owner signup policy configured.")


if __name__ == "__main__":
    main()
