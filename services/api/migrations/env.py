from alembic import context
from sqlalchemy import create_engine, text
from scos.config import DATABASE_URL, DATABASE_SCHEMA, validate, database_connect_args

validate()
engine = create_engine(DATABASE_URL.replace("postgresql://", "postgresql+psycopg://"), connect_args=database_connect_args())
with engine.connect() as connection:
    if DATABASE_SCHEMA != "public":
        q = connection.dialect.identifier_preparer.quote
        connection.exec_driver_sql("SET search_path TO " + q(DATABASE_SCHEMA) + ", public")
        connection.commit()
        if connection.execute(text("SELECT current_schema()")).scalar_one() != DATABASE_SCHEMA:
            raise RuntimeError("SCOS_RESOURCE_ISOLATION: migration schema was not selected")
        connection.commit()
    context.configure(connection=connection, version_table_schema=DATABASE_SCHEMA)
    with context.begin_transaction():
        context.run_migrations()
