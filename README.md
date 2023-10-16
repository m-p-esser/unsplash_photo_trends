# Unsplash Photo Trends

![Unsplash Cover Photo](https://github.com/m-p-esser/unsplash_photo_trends/blob/master/docs/images/unsplash_cover_image.png)

## What is this Project about?

This Project is a Data Enginering Project about **collecting photo metadata** and actual **photos** from the **Unsplash Photo Platform**. Unsplash offers photos for download under a free licensing model.

The Project is mostly written in Python, uses [Prefect](https://www.prefect.io/) for Data Orchestration and Google Cloud Storage and Google BigQuery as main storage technologies. The Jobs are scheduled either daily or in 10-60 minute intervals and are executed trough Google Cloud Runs.

## Statistics
- XXX.XXX Photos
- XXX.XXX Metadata about Photos
  - including Views, Likes, Downloads, EXIF, Location

## Data Pipeline
The Data Pipeline consist of 5 different Flows (Jobs)

![Deployments](https://github.com/m-p-esser/unsplash_photo_trends/blob/master/docs/images/deployments.png)

### Pipeline Design
- [ ] Add Obsidian Canvas here

## Technology 

**Storage**
- [Google Cloud Storage](https://cloud.google.com/storage?hl=en)
- [Google BigQuery](https://cloud.google.com/bigquery?hl=en)

**Compute**
- [Google Cloud Run](https://cloud.google.com/run?hl=en)

**Orchestration**
- [Prefect](https://www.prefect.io/)

**Languages**
- Python
- Bash
- SQL

## Prerequisites

If you want to reproduce some of this code or copy and paste parts of it, feel free to do so.

If you want to build on this projects, here are the prerequisites

- A Google account (to create ressources in GCP)
- A Prefect account (with access to the Prefect Cloud)
- Expects the following Git branches. See [Git Branching Strategy](https://github.com/m-p-esser/unsplash_photo_trends/blob/master/docs/images/Data_Engineering_Git_Branching_Strategy.png):
  - master
  - develop
  - test 

## Folder structure

These are the main folders (and their their descrptions) of this Github repo. In case some folders are not visible, then they are not meant to be shared (see `.gitignore`) 

*hint: `tree -L 2 -d -A`* 

```
.
└── .github          --> Github actions (e.g. CI)
├── data             --> Data in different stages (raw, staged, final)
│   ├── 00_raw       --> Immutable, raw data
│   ├── 01_staged    --> Processed data
│   └── 02_final     --> Data which can be served (ML, Analytics)
├── docs
│   └── images       --> Images used in this Readme.md
├── images           --> Docker Images (which are used across flows)
├── make             --> Makefiles for setting up ressources and environment
├── output           --> Deliverables in form of reports or models
│   ├── models
│   └── reports
├── references       --> Data dictionaries, manuals, and all other explanatory materials
├── src              --> Source code (Python)
│   ├── blocks       --> Prefect Blocks
│   ├── etl          --> Collection of common Extraction, Transformation and Loading functions used
│   ├── prefect      --> Prefect Flows
│   └── scripts      --> Python and Bash utility scripts
├── tests            --> Unit tests
```

## Most important files on root level

- `prefect.yaml`: Deployment steps and configuration
- `.pre-commit-config.yaml`: Pre-commit hooks which are run before each commit
- `Makefile`: Settings for Makefile (which are stored in folder `make/*`)
- `pyproject.toml` & `poetry.lock`: Python dependencies 

## Setup

### Activate Pre-commit 
Install Pre-commit hooks (for code formatting, import statement checks before committing)
- `pre-commit install`

### Environment Variables
Define values in `base.env` (not part of this repository)
For reference check `base.env.example` which contains all major variables required for this project

### Github Action Secrets
Add the following Secrets as Action secrets to your Github repository: 
- `PREFECT_API_KEY`
- `PREFECT_API_URL`

See https://docs.prefect.io/latest/api-ref/rest-api/#finding-your-prefect-cloud-details

### GCP Setup
Run `make setup-gcp` to setup up the Google Cloud Project

If this doesn't work, run the commands from `00_setup_gcp.mk` command by command in the following order:
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
- `make env-init` to prepare ENV environment variable
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
- Deploy Flow by running `make deploy-flow`
- Run integration test trough a manual Flow run
- Sync with Bigquery (using existing Flow if you want to sync GCS and Bigquery using a Push pattern)

Move on `prod`
- Merge with `test`
- Deploy Flow by running `make deploy-flow`

