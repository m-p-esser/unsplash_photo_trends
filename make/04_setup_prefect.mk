##@ [Prefect: Setup]

.PHONY: set-prefect-env-variarables
set-prefect-env-variarables: ## Set Environment variables for Prefect
	prefect config set PREFECT_LOGGING_EXTRA_LOGGERS=${PREFECT_LOGGING_EXTRA_LOGGERS}
	prefect config set PREFECT_API_URL=${PREFECT_API_URL}
	prefect config set PREFECT_API_KEY=${PREFECT_API_KEY}

.PHONY: create-prefect-blocks
create-prefect-blocks: ## Create Prefect Blocks
	make env-init
	prefect block register --file src/blocks/create_gcp_credentials.py
	prefect block register --file src/blocks/create_github.py
	prefect block register --file src/blocks/create_google_cloud_run.py
	prefect block register --file src/blocks/create_unsplash_access_key.py
	prefect block register --file src/blocks/create_bigquery.py
	prefect block register --file src/blocks/create_zenrows_api_key.py
	prefect block register --file src/blocks/create_bright_data_secrets.py
	prefect block register --file src/blocks/create_vertex_ai.py

.PHONY: create-prefect-artifact-repository
create-prefect-artifact-repository: ## Create GCP Artificat Repository for Prefect Flows
	make env-init
	gcloud artifacts repositories create prefect-$(ENV) --repository-format DOCKER --location $(GCP_DEFAULT_REGION)
	gcloud auth configure-docker \
		$(GCP_DEFAULT_REGION)-docker.pkg.dev

# @see https://docs.prefect.io/latest/concepts/work-pools/
.PHONY: create-google-cloud-run-push-work-pool
create-google-cloud-run-push-work-pool: ## Create Google Cloud Run Workflow (for Agentless deployment)
	make env-init
	prefect work-pool create $(ENV)-cloud-run-push-work-pool \
		--type cloud-run:push
# Need to manually add GCP Credentials under Work Pool Settings

.PHONY: setup-compute-engine
setup-compute-engine: ## Create a GCP VM which triggers Flow runs 
	gcloud compute instances create-with-container prefect-${ENV}-vm \
			--container-image $(GCP_DEFAULT_REGION)-docker.pkg.dev/$(GCP_PROJECT_ID)/prefect-${ENV}/prefect:$(PREFECT_VERSION)-python$(PYTHON_VERSION) \
			--container-mount-host-path=host-path=/var/run/docker.sock,mount-path=/var/run/docker.sock,mode=rw \
			--container-privileged \
			--container-env PREFECT_API_URL=${PREFECT_API_URL} \
			--container-env PREFECT_API_KEY=${PREFECT_API_KEY} \
			--container-command="prefect" \
			--container-arg="worker" \
			--container-arg="start" \
			--container-arg="--pool" \
			--container-arg="${ENV}-vertex-ai-work-pool" \
			--container-restart-policy='always' \
			--boot-disk-size="200Gi" \
			--machine-type="e2-micro" \
			--zone=$(GCP_DEFAULT_ZONE)

.PHONY: setup-prefect
setup-prefect: ## Setup Prefect Blocks, Artifact Repo and Work Pools	
	@echo "Setting Environment variables for Prefect"
	"$(MAKE)" set-prefect-env-variarables
	@echo "Creating Prefect Blocks"
	"$(MAKE)" create-prefect-blocks
	@echo "Create Artificat Repository for Prefect Flows"
	"$(MAKE)" create-prefect-artifact-repository
	@echo "Create Push Work Pool for Google Cloud Run (be sure to add GCP Credentials manually)"
	"$(MAKE)" create-google-cloud-run-push-work-pool
