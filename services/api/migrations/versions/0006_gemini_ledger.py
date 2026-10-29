from alembic import op
from sqlalchemy import text

revision = "scos_0006"
down_revision = "scos_0005"


def upgrade():
    op.execute("""CREATE TABLE ai_draft_calls (
      id uuid PRIMARY KEY DEFAULT gen_random_uuid(), actor_id uuid NOT NULL REFERENCES app_users(id),
      variant_id uuid NOT NULL REFERENCES campaign_variants(id), idempotency_key text NOT NULL,
      request_sha256 text NOT NULL, input_snapshot jsonb NOT NULL, input_sha256 text NOT NULL,
      model_id text NOT NULL, price_snapshot jsonb NOT NULL, estimated_cost numeric(18,6) NOT NULL,
      status text NOT NULL CHECK(status IN ('submitting','succeeded','failed','unknown','applied')),
      output jsonb, provider_receipt text, model_version text, usage jsonb,
      amount_usd numeric(18,6), error_code text,
      created_at timestamptz NOT NULL DEFAULT now(), finished_at timestamptz,
      UNIQUE(actor_id,idempotency_key));
      CREATE UNIQUE INDEX idx_ai_unresolved ON ai_draft_calls(variant_id,input_sha256)
        WHERE status IN ('submitting','unknown');
      CREATE TABLE ai_call_reservations (
        call_id uuid NOT NULL REFERENCES ai_draft_calls(id),
        reservation_id uuid NOT NULL REFERENCES cost_reservations(id),
        PRIMARY KEY(call_id,reservation_id));""")
    c = op.get_bind()
    schema = c.execute(text("SELECT current_schema()")).scalar_one()
    if schema != "public":
        q = c.dialect.identifier_preparer.quote
        for table in ("ai_draft_calls", "ai_call_reservations"):
            c.exec_driver_sql(f"ALTER TABLE {q(schema)}.{q(table)} ENABLE ROW LEVEL SECURITY")
            for role in ("anon", "authenticated"):
                c.exec_driver_sql(f"REVOKE ALL ON {q(schema)}.{q(table)} FROM {q(role)}")


def downgrade():
    raise RuntimeError("Usage ledger downgrade is disabled")
