.PHONY: install infra migrate dev down lint test test-backend test-security test-faults test-contracts test-media build backup restore-drill
install:
	uv sync --frozen
	npm --prefix apps/web ci --no-fund --no-audit
infra:
	docker compose up -d --wait postgres
migrate:
	uv run alembic upgrade head
dev:
	python3 scripts/dev.py
down:
	python3 scripts/stop.py
	docker compose stop postgres
lint:
	uv run ruff check services/api scripts
	npm --prefix apps/web run typecheck
test: test-backend

test-backend:
	uv run python scripts/prepare_test_db.py
	uv run pytest -q --junitxml=artifacts/backend-tests.xml
test-security:
	uv run python scripts/prepare_test_db.py
	uv run pytest services/api/tests/test_security.py -q
test-faults:
	uv run python scripts/prepare_test_db.py
	uv run pytest services/api/tests/test_faults.py -q
test-contracts:
	PYTHONPATH=services/api uv run python scripts/contracts.py
test-media:
	PYTHONPATH=services/api uv run python scripts/verify_media.py
build:
	npm --prefix apps/web run build
backup:
	PYTHONPATH=services/api uv run python scripts/backup.py
restore-drill:
	PYTHONPATH=services/api uv run python scripts/backup.py --restore-drill

.PHONY: test-e2e audit-blueprint
test-e2e:
	npm --prefix apps/web run test:e2e
audit-blueprint:
	uv run python scripts/audit_blueprint.py
