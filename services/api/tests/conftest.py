import os

os.environ["SCOS_DATABASE_URL"] = "postgresql://scos:scos_local_only@127.0.0.1:55432/scos_test"
os.environ["SCOS_S3_BUCKET"] = "scos-test"
import pytest
from psycopg import sql
from scos.db import connect, all_rows
from scos.seed import bootstrap
from scos import storage


@pytest.fixture(autouse=True)
def isolated_database():
    storage.init()
    with connect() as c:
        assert c.info.dbname == "scos_test"
        tables = all_rows(
            c, "SELECT tablename FROM pg_tables WHERE schemaname='public' AND tablename!='alembic_version'"
        )
        c.execute(
            sql.SQL("TRUNCATE {} RESTART IDENTITY CASCADE").format(
                sql.SQL(",").join(sql.Identifier(t["tablename"]) for t in tables)
            )
        )
        bootstrap(c)
    yield


@pytest.fixture
def conn():
    with connect() as c:
        yield c
