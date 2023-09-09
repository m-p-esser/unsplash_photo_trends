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
	make env-init
	python3 src/prefect/ingest_topics_gcs.py