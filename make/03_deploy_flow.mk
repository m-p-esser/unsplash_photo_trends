##@ [Flow: Deployment]

.PHONY: push-prefect-runner-image
push-prefect-runner-image: ## Deploy Prefect Runner Image (generic Prefect image to run all flows)
	make env-init
	poetry export -o requirements.txt --without-hashes --without-urls --without=dev,test
	docker build -t $(GCP_DEFAULT_REGION)-docker.pkg.dev/$(GCP_PROJECT_ID)/prefect-${ENV}/prefect:$(PREFECT_VERSION)-python$(PYTHON_VERSION) \
		--build-arg PYTHON_VERSION=${PYTHON_VERSION} \
		--build-arg PREFECT_VERSION=${PREFECT_VERSION} \
		-f images/prefect_runner/Dockerfile .
	docker push $(GCP_DEFAULT_REGION)-docker.pkg.dev/$(GCP_PROJECT_ID)/prefect-${ENV}/prefect:$(PREFECT_VERSION)-python$(PYTHON_VERSION)

# @see https://crontab.guru/ for how to write cron expressions
.PHONY: deploy-ingest-topics-gcs
deploy-ingest-topics-gcs: ## Deploy Ingest Topic GCS Flow as Google Cloud Run
	make env-init
	make push-prefect-runner-image
	prefect deployment build src/prefect/ingest_topics_gcs.py:ingest_topics_gcs \
		--name ingest-topics-gcs-${ENV} \
		--infra-block cloud-run-job/${GCP_PROJECT_ID}-google-cloud-run-${ENV} \
		--storage-block github/${GCP_PROJECT_ID}-github-${ENV} \
		--output deployments/ingest-topics-gcs-${ENV}-deployment.yaml \
		--pool ${ENV}-cloud-run-push-work-pool \
		--cron "0 9 * * *" \
		--timezone 'Europe/Berlin' \
		--apply

.PHONY: deploy-healthcheck
deploy-healthcheck: ## Deploy Healtcheck Flow as Google Cloud Run
	make env-init
	make push-prefect-runner-image
	prefect deployment build src/prefect/healthcheck.py:healthcheck \
		--name healthcheck-${ENV} \
		--infra-block cloud-run-job/${GCP_PROJECT_ID}-google-cloud-run-${ENV} \
		--storage-block github/${GCP_PROJECT_ID}-github-${ENV} \
		--output deployments/healthcheck-${ENV}-deployment.yaml \
		--pool ${ENV}-cloud-run-push-work-pool \
		--cron "0 8 * * *" \
		--timezone 'Europe/Berlin' \
		--apply

.PHONY: deploy-ingest-monthly-platform-stats-gcs
deploy-ingest-monthly-platform-stats-gcs: ## Deploy Ingest Topic GCS Flow as Google Cloud Run
	make env-init
	make push-prefect-runner-image
	prefect deployment build src/prefect/ingest_monthly_platform_stats_gcs.py:ingest_monthly_platform_stats_gcs \
		--name ingest-monthly-platform-stats-gcs-${ENV} \
		--infra-block cloud-run-job/${GCP_PROJECT_ID}-google-cloud-run-${ENV} \
		--storage-block github/${GCP_PROJECT_ID}-github-${ENV} \
		--output deployments/ingest-topics-gcs-${ENV}-deployment.yaml \
		--pool ${ENV}-cloud-run-push-work-pool \
		--cron "0 8 * * *" \
		--timezone 'Europe/Berlin' \
		--apply

.PHONY: deploy-ingest-photos-gcs
deploy-ingest-photos-gcs: ## Deploy Ingest Topic GCS Flow as Google Cloud Run
	make env-init
	make push-prefect-runner-image
	prefect deployment build src/prefect/ingest_photos_gcs.py:ingest_photos_gcs \
		--name ingest-photos-gcs-${ENV} \
		--infra-block cloud-run-job/${GCP_PROJECT_ID}-google-cloud-run-${ENV} \
		--storage-block github/${GCP_PROJECT_ID}-github-${ENV} \
		--output deployments/ingest-topics-gcs-${ENV}-deployment.yaml \
		--pool ${ENV}-cloud-run-push-work-pool \
		--params='{"gcp_credential_block_name": "unsplash-photo-trends-deployment-sa"}' \
		--cron "*/15 * * * *" \
		--timezone 'Europe/Berlin' \
		--apply

.PHONY: deploy-sync-topics-gcs-to-bigquery
deploy-sync-gcs-to-bigquery: ## Sync Google Cloud Storage and Bigquery
	make env-init
	make push-prefect-runner-image
	prefect deployment build src/prefect/sync_gcs_to_bigquery.py:sync_gcs_to_bigquery \
		--name sync-gcs-to-bigquery \
		--infra-block cloud-run-job/${GCP_PROJECT_ID}-google-cloud-run-${ENV} \
		--storage-block github/${GCP_PROJECT_ID}-github-${ENV} \
		--output deployments/sync-gcs-to-bigquery-deployment.yaml \
		--pool ${ENV}-cloud-run-push-work-pool \
		--params='{"table_name": "topics", "source_uri": "gs://unsplash-topics-${ENV}/*.parquet", "file_format": "PARQUET"}' \
		--apply