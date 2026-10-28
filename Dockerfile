FROM python:3.13-slim-bookworm@sha256:281d39ff02e3b389401586134ff9e6572954687822a58055ec07a60ded4e0b7f
ENV PYTHONUNBUFFERED=1 PYTHONPATH=/app/services/api UV_LINK_MODE=copy SCOS_RUNTIME_DIR=/app/.runtime
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg fonts-dejavu-core espeak-ng ca-certificates \
    && rm -rf /var/lib/apt/lists/* && pip install --no-cache-dir uv==0.7.13
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev
COPY . .
RUN groupadd --gid 10001 scos && useradd --uid 10001 --gid scos --create-home scos \
    && mkdir -p /app/.runtime && chown -R scos:scos /app/.runtime /app/.venv
USER scos
EXPOSE 8080
CMD ["sh", "-c", "uv run --no-sync python scripts/migrate.py && exec uv run --no-sync uvicorn scos.app:app --host 0.0.0.0 --port ${PORT:-8080} --no-access-log"]
