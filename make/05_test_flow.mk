##@ [Flow: Test]

.PHONY: run-unit-tests
run-unit-tests: ## Run all Unit Tests
# gh workflow run "Unit Test Prefect Flows" // Currently not working altough dispatcher has been added
	make env-init
	pytest -v

.PHONY: integration-test-healthcheck
integration-test-healthcheck: ## Integration Test Healthcheck Flow
	make env-init
	python3 src/prefect/healthcheck.py

.PHONY: integration-test-ingest-topics-gcs
integration-test-ingest-topics-gcs: ## Integration Test Ingest Topics GCS Flow
	make deploy-ingest-topics-gcs
	prefect deployment run ingest-topics-gcs/ingest-topics-gcs-${ENV}

.PHONY: integration-test-ingest-monthly-platform-stats-gcs
integration-test-ingest-monthly-platform-stats-gcs: ## Integration Test Ingest Monthly Platform Stats GCS Flow
	make deploy-ingest-monthly-platform-stats-gcs
	prefect deployment run ingest-monthly-platform-stats-gcs/ingest-monthly-platform-stats-gcs-${ENV}

.PHONY: integration-test-ingest-photos-gcs
integration-test-ingest-photos-gcs: ## Integration Test Ingest Photos GCS Flow
	make deploy-ingest-photos-gcs
	prefect deployment run ingest-photos-gcs/ingest-photos-gcs-${ENV}