##@ [Prefect: Setup]

.PHONY: create-prefect-blocks
create-prefect-blocks: ## Create Prefect Blocks
	python3 src/scripts/create_blocks.py

.PHONY: create-prefect-artifact-repository
create-prefect-artifact-repository: ## Create GCP Artificat Repository for Prefect Flows
	gcloud artifacts repositories create prefect-$(ENV) --repository-format DOCKER --location $(GCP_DEFAULT_REGION)
	gcloud auth configure-docker \
		$(GCP_DEFAULT_REGION)-docker.pkg.dev

# @see https://docs.prefect.io/latest/concepts/work-pools/
.PHONY: create-google-cloud-run-push-work-pool
create-google-cloud-run-push-work-pool: ## Create Google Cloud Run Workflow (for Agentless deployment)
	prefect work-pool create dev-cloud-run-push-work-pool \
		--type cloud-run:push
# Need to manually add GCP Credentials under Work Pool Settings

.PHONY: setup-prefect
setup-prefect: ## Setup Prefect Blocks, Artifact Repo and Work Pools	
	@echo "Creating Prefect Blocks"
	"$(MAKE)" create-prefect-blocks
	@echo "Create Artificat Repository for Prefect Flows"
	"$(MAKE)" create-prefect-artifact-repository
	@echo "Create Push Work Pool for Google Cloud Run (be sure to add GCP Credentials manually)"
	"$(MAKE)" create-google-cloud-run-push-work-pool
