from alembic import op
from scos.config import ROOT

revision = "scos_0001"
down_revision = None


def upgrade():
    ddl = (ROOT / "docs/blueprint/03_DATABASE_SCHEMA.sql").read_text()
    ddl = ddl.replace("BEGIN;", "").replace("COMMIT;", "")
    op.get_bind().exec_driver_sql(ddl)


def downgrade():
    raise RuntimeError("Destructive downgrade disabled; restore into an isolated database instead.")
