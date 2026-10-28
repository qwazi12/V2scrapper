import os
import subprocess
import sys
import psycopg

url = "postgresql://scos:scos_local_only@127.0.0.1:55432/"
with psycopg.connect(url + "postgres", autocommit=True) as c:
    if not c.execute("SELECT 1 FROM pg_database WHERE datname='scos_e2e'").fetchone():
        c.execute("CREATE DATABASE scos_e2e")
env = dict(
    os.environ,
    SCOS_DATABASE_URL=url + "scos_e2e",
    SCOS_S3_BUCKET="scos-e2e",
    SCOS_ENV="local",
    SCOS_RESOURCE_NAMESPACE="scos-local",
)
subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], env=env, check=True)
print("Isolated scos_e2e database ready. Local application database was not changed.")
