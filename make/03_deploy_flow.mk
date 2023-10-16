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

.PHONY: deployment-preperations
deployment-preperations: ## Preperation steps before deploying
	make env-init
	poetry export -o requirements.txt --without-hashes --without-urls --without=dev,test

.PHONY: deploy-flow
deploy-flow: ## Deploy any flow
	make deployment-preperations
	python src/scripts/create_env_variable.py
	prefect deploy

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