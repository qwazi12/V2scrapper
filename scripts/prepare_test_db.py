import os
import subprocess
import sys
import psycopg

url = "postgresql://scos:scos_local_only@127.0.0.1:55432/"
with psycopg.connect(url + "postgres", autocommit=True) as c:
    if not c.execute("SELECT 1 FROM pg_database WHERE datname='scos_test'").fetchone():
        c.execute("CREATE DATABASE scos_test")
env = dict(os.environ, SCOS_DATABASE_URL=url + "scos_test", SCOS_S3_BUCKET="scos-test")
subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], env=env, check=True)
print("Isolated scos_test database migrated.")
