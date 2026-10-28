from alembic import op

revision = "scos_0002"
down_revision = "scos_0001"


def upgrade():
    op.execute("""CREATE TABLE mock_provider_receipts (
      intent_id uuid PRIMARY KEY REFERENCES publication_attempts(id),
      external_post_id text NOT NULL UNIQUE, account_id uuid NOT NULL REFERENCES social_accounts(id),
      export_sha256 text NOT NULL, accepted_at timestamptz NOT NULL DEFAULT now(),
      submit_count integer NOT NULL DEFAULT 1 CHECK(submit_count=1));""")
    op.execute(
        "CREATE UNIQUE INDEX idx_scos_render_dedupe ON jobs(kind,input_hash) WHERE kind='render' AND status NOT IN ('failed','cancelled','dead_letter')"
    )


def downgrade():
    op.execute("DROP INDEX idx_scos_render_dedupe")
    op.execute("DROP TABLE mock_provider_receipts")
