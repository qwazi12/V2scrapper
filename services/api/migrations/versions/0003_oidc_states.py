from alembic import op

revision = "scos_0003"
down_revision = "scos_0002"


def upgrade():
    op.execute("""CREATE TABLE oidc_login_states (
      state_hash bytea PRIMARY KEY, browser_hash bytea NOT NULL,
      nonce text NOT NULL, code_verifier text NOT NULL,
      expires_at timestamptz NOT NULL, used_at timestamptz,
      created_at timestamptz NOT NULL DEFAULT now());""")
    op.execute("CREATE INDEX idx_oidc_states_expiry ON oidc_login_states(expires_at)")


def downgrade():
    op.execute("DROP TABLE oidc_login_states")
