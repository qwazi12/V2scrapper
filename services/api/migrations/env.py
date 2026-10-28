from alembic import context
from sqlalchemy import create_engine
from scos.config import DATABASE_URL, validate

validate()
engine = create_engine(DATABASE_URL.replace("postgresql://", "postgresql+psycopg://"))
with engine.connect() as connection:
    context.configure(connection=connection)
    with context.begin_transaction():
        context.run_migrations()
