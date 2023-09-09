##@ [Flow: Deployment]

.PHONY: push-prefect-runner-image
push-prefect-runner-image: ## Deploy Prefect Runner Image (generic Prefect image to run all flows)
	poetry export -o requirements.txt --without-hashes --without-urls --without=dev,test
	docker build -t $(GCP_DEFAULT_REGION)-docker.pkg.dev/$(GCP_PROJECT_ID)/prefect-${ENV}/prefect:$(PREFECT_VERSION)-python$(PYTHON_VERSION) \
		--build-arg PYTHON_VERSION=${PYTHON_VERSION} \
		--build-arg PREFECT_VERSION=${PREFECT_VERSION} \
		-f images/prefect_runner/Dockerfile .
	docker push $(GCP_DEFAULT_REGION)-docker.pkg.dev/$(GCP_PROJECT_ID)/prefect-${ENV}/prefect:$(PREFECT_VERSION)-python$(PYTHON_VERSION)

# @see https://crontab.guru/ for how to write cron expressions
.PHONY: deploy-ingest-topics-gcs
deploy-ingest-topics-gcs: ## Deploy Ingest Topic GCS Flow as Google Cloud Run
	prefect deployment build src/prefect/ingest_topics_gcs.py:ingest_topics_gcs \
		--name ingest-topics-gcs-${ENV} \
		--infra-block cloud-run-job/${GCP_PROJECT_ID}-google-cloud-run-${ENV} \
		--storage-block github/${GCP_PROJECT_ID}-github-${ENV} \
		--output deployments/ingest-topics-gcs-${ENV}-deployment.yaml \
		--pool ${ENV}-cloud-run-push-work-pool \
		--cron "0 9 * * *" \
		--apply

.PHONY: deploy-healthcheck
deploy-healthcheck: ## Deploy Healtcheck Flow as Google Cloud Run
	prefect deployment build src/prefect/healthcheck.py:healthcheck \
		--name healthcheck-${ENV} \
		--infra-block cloud-run-job/${GCP_PROJECT_ID}-google-cloud-run-${ENV} \
		--storage-block github/${GCP_PROJECT_ID}-github-${ENV} \
		--output deployments/healthcheck-${ENV}-deployment.yaml \
		--pool ${ENV}-cloud-run-push-work-pool \
		--cron "0 8 * * *" \
		--apply
