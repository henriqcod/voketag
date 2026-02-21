.PHONY: build scan-service factory-service blockchain-service docker-up docker-down migrate migrate-create test lint restore-test verify-backups

build: scan-service factory-service blockchain-service

scan-service:
	cd services/scan-service && go build -o ../../bin/scan-service ./cmd

factory-service:
	cd services/factory-service && pip install -r requirements.txt

blockchain-service:
	cd services/blockchain-service && pip install -r requirements.txt

docker-up:
	docker compose -f infra/docker/compose.yml up -d

docker-down:
	docker compose -f infra/docker/compose.yml down

test:
	@echo "Running tests..."
	cd services/scan-service && go test ./... -v
	cd services/factory-service && pytest -v

lint:
	@echo "Running linters..."
	cd services/scan-service && go vet ./...
	cd services/factory-service && ruff check .

migrate:
	@echo "Running database migrations..."
	cd services/factory-service && alembic upgrade head

migrate-create:
	@echo "Creating new migration..."
	@read -p "Migration description: " desc; \
	cd services/factory-service && alembic revision -m "$$desc"

restore-test:
	@echo "Running database restore test..."
	@bash scripts/restore_test.sh

verify-backups:
	@echo "Verifying backups..."
	@gcloud sql backups list --instance=voketag-postgres
	@echo ""
	@echo "Checking PITR coverage..."
	@gcloud sql instances describe voketag-postgres \
		--format="get(settings.backupConfiguration.pointInTimeRecoveryEnabled)"

.DEFAULT_GOAL := help

help:
	@echo "VokeTag 2.0 - Makefile commands"
	@echo ""
	@echo "Available commands:"
	@echo "  make build          - Build all services"
	@echo "  make docker-up      - Start all services with Docker Compose"
	@echo "  make docker-down    - Stop all services"
	@echo "  make test           - Run tests"
	@echo "  make lint           - Run linters"
	@echo "  make migrate        - Run database migrations"
	@echo "  make migrate-create - Create new migration"
	@echo "  make restore-test   - Run database restore test"
	@echo "  make verify-backups - Verify backup integrity"
