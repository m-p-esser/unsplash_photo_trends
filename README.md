# Unsplash Photo Trends

![Unsplash Cover Photo](https://github.com/m-p-esser/unsplash_photo_trends/blob/master/docs/images/unsplash_cover_image.png):

## What is this Project about?

This Project is about collecting Photo metadata from the Unsplash Photo Platform. Unsplash offers photos for download under a free licensing model.

## Prerequisites
- A Google account (to create ressources in GCP)
- A Prefect account (with access to the Prefect Cloud)
- Expects the following Git branches. See [Git Branching Strategy](https://github.com/m-p-esser/unsplash_photo_trends/blob/master/docs/images/Data_Engineering_Git_Branching_Strategy.png):
  - master
  - develop
  - test 

## Folder structure

*hint: `tree -L 2 -d -A`* 

```
.
└── .github          --> Github actions (e.g. CI)
├── data             --> Data in different stages (raw, staged, final)
│   ├── 00_raw       --> Immutable, raw data
│   ├── 01_staged    --> Processed data
│   └── 02_final     --> Data which can be served (ML, Analytics)
├── deployments      --> Prefect deployment .yaml files
├── docs
│   └── images
├── images           --> Docker Images (which are used across flows)
├── make             --> Makefiles for setting up ressources and environment
├── output           --> Deliverables in form of reports or models
│   ├── models
│   └── reports
├── references       --> Data dictionaries, manuals, and all other explanatory materials
├── src              --> Source code (Python)
│   ├── blocks       --> Prefect Blocks
│   ├── etl          --> Collection of common Extraction, Transformation and Loading functions
│   ├── prefect      --> Prefect Flows
│   └── scripts      --> Python and Bash utility scripts
├── tests            --> Unit tests
```

## Most important files on root level
`.pre-commit-config.yaml`: Pre-commit hooks which are run before each commit
`prefect.yaml`: Deployment steps and configuration
`Makefile`: Settings for Makefile (which are stored in folder `make/*`)
`pyproject.toml` & `poetry.lock`: Python dependencies 

## Setup

### Activate Pre-commit 
Install Pre-commit hooks (for code formatting, import statement checks before committing)
- `pre-commit install`

### Environment Variables
Define values in base.env (not part of this repository)

### Github Action Secrets
Add the following Secrets as Action secrets to your Github repository: 
- PREFECT_API_KEY
- PREFECT_API_URL

See https://docs.prefect.io/latest/api-ref/rest-api/#finding-your-prefect-cloud-details

### GCP Setup
Run `make setup-gcp` to setup up the Google Cloud Project

If this doesn't work, run the commands from `01_setup_gcp.mk` command by command in the following order:
- `make create-gcp-project`
- `make set-default-gcp-project`
- `make link-project-to-billing-account`
- `make create-deployment-service-account`
- `make create-deployment-service-account-key-file`
- `make enable-gcp-services`
- `make bind-iam-policies-to-deployment-service-account`
- `make set-deployment-service-account-as-default`

### Environment Setup
*necessary everytime you start working on the project*
- `make dev-init` to setup development environment

### Prefect Setup
As mentioned above, this project requires a Prefect account and access to the Prefect Cloud
- `make setup-prefect` 

### Setup Storage
Setup the storage infrastructure by running
- `make create-gcs-buckets`

### Deployment and Testing

Start on `develop`
- Write Tasks and Flows
- If necessary write Unit Tests
- Run `make run-unit-tests`

Move on to `test`
- Merge with `develop`
- Run Integration Tests (ensures that the Docker image is updated in Artifact Registry) which also deploys the flow
- Deploy Flow by running `make deploy-flow`
- Sync with Bigquery (using existing Flow)

Move on `prod`
- Repeat the steps from `test`

