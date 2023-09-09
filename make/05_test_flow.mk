##@ [Flow: Test]

.PHONY: run-unit-tests
run-unit-tests: ## Run all Unit Tests
# gh workflow run "Unit Test Prefect Flows" // Currently not working altough dispatcher has been added
	pytest -v

.PHONY: integration-test-healthcheck
integration-test-healthcheck: ## Integration Test Healthcheck Flow
	python3 src/prefect/healthcheck.py

.PHONY: integration-test-ingest-topics-gcs
integration-test-ingest-topics-gcs: ## Integration Test Ingest Topics GCS Flow
	python3 src/prefect/ingest_topics_gcs.py