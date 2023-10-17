# Unsplash Photo Trends

![Unsplash Cover Photo](https://github.com/m-p-esser/unsplash_photo_trends/blob/master/docs/images/unsplash_cover_image.png)

## <a name='TableofContents'></a>Table of Contents

<!-- vscode-markdown-toc -->
* 1. [Table of Contents](#TableofContents)
* 2. [What is this Project about?](#WhatisthisProjectabout)
* 3. [The Dataset in numbers](#TheDatasetinnumbers)
* 4. [Data Flow Diagramm (DFD)](#DataFlowDiagrammDFD)
* 5. [Data Model](#DataModel)
* 6. [Deployments *(Flows)*](#DeploymentsFlows)
* 7. [Technology](#Technology)
* 8. [Prerequisites](#Prerequisites)
* 9. [Folder structure](#Folderstructure)
* 10. [Most important files on root level](#Mostimportantfilesonrootlevel)
* 11. [Setup](#Setup)
	* 11.1. [Activate Pre-commit](#ActivatePre-commit)
	* 11.2. [Environment Variables](#EnvironmentVariables)
	* 11.3. [Github Action Secrets](#GithubActionSecrets)
	* 11.4. [GCP Setup](#GCPSetup)
	* 11.5. [Environment Setup](#EnvironmentSetup)
	* 11.6. [Prefect Setup](#PrefectSetup)
	* 11.7. [Setup Storage](#SetupStorage)
	* 11.8. [Deployment and Testing](#DeploymentandTesting)

<!-- vscode-markdown-toc-config
	numbering=true
	autoSave=true
	/vscode-markdown-toc-config -->
<!-- /vscode-markdown-toc -->

<br>

## <a name='WhatisthisProjectabout'></a>What is this Project about?

Ever wondered **which** type of **photos are downloaded the most often**? Look no further. This project aims to deliver the answer to this question. 

This Project is a <u>**Data Enginering Project**</u> about **collecting photo metadata** and actual **photos** from the **Unsplash Photo Platform**. Unsplash offers photos for download under a free licensing model.

The Project is mostly written in Python, uses [Prefect](https://www.prefect.io/) for Data Orchestration and Google Cloud Storage and Google BigQuery as main storage technologies. The Jobs are scheduled either daily or in 10-60 minute intervals and are executed trough Google Cloud Runs.

<br>

## <a name='TheDatasetinnumbers'></a> :1234: The Dataset in numbers
*Last Update on 17th October, 2023*
- 243.000 **Photos**
- 243.000 **Metadata** about Photos
  - including Views, Likes, Downloads, EXIF, Location, User
- **Daily Platform Stats**
  - including number of views/downloads, new photos, new photographers etc

<br>


## <a name='DataFlowDiagrammDFD'></a> :arrow_right: Data Flow Diagramm (DFD)

**Just the `EL`** part of `ELT` is **done in this project**. 

**Google Cloud Storage** is used as initial, immutable raw data layer (`E`).

**BigQuery** is used for two purposes: 
1. to log which photos have already been requested. This logs are checked in each run, so the same image won't get requested twice.
2. to serve as intermediata storage (`L`). The actual data requires further processing and transformation (`T`) to be suitable for data analysis.

The following diagram describes the flow of data from different API endpoints to different storages.

![DFD](https://raw.githubusercontent.com/m-p-esser/unsplash_photo_trends/master/docs/images/dataflow_diagram.png)

A scrollable/zoomable version can be found [here](https://lucid.app/lucidchart/9850ca3d-b10c-467c-b45a-238ff971833e/edit?viewport_loc=-3868%2C-1072%2C6376%2C3204%2C0_0&invitationId=inv_82e52a93-d67c-443a-a50d-1ead80641fcd) (Lucid account required)

<br>


## <a name='DataModel'></a> :globe_with_meridians: Data Model

The most important table is `photo-editorial-metadata-expanded` which contains Photo metadata from the *Editorial* section of Unsplash. 

*Editorial photos can only be used in editorial projects such as: news related materials (newspaper and magazine articles, TV news), blogs and educational materials.*

![Data Model](https://raw.githubusercontent.com/m-p-esser/unsplash_photo_trends/master/docs/images/data_model.png)

Additional tables not shown in this diagram as they are external tables syncing data from Google Cloud Storage to Big Query and are not being picked up by ERM modeling software are:
- [`monthly-platform-stats`](https://raw.githubusercontent.com/m-p-esser/unsplash_photo_trends/master/docs/images/monthly-platform-stats.png)
- [`topics`](https://raw.githubusercontent.com/m-p-esser/unsplash_photo_trends/master/docs/images/topics.png)

<br>

## <a name='DeploymentsFlows'></a> :rocket: Deployments *(Flows)*
The Data Pipeline consist of 5 different Flows. A Flow in the context of Prefect is comparable to an ETL Job. Ignore the `healhcheck-prod` Flow (which just checks network/machine accesibility)

![Deployments](https://raw.githubusercontent.com/m-p-esser/unsplash_photo_trends/master/docs/images/deployments.png)

<br>

## <a name='Technology'></a> :satellite: Technology 

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

## <a name='Prerequisites'></a>Prerequisites

If you want to reproduce some of this code or copy and paste parts of it, feel free to do so.

If you want to build on this projects, here are the prerequisites

- A Google account (to create ressources in GCP)
- A Prefect account (with access to the Prefect Cloud)
- Expects the following Git branches. See [Git Branching Strategy](https://github.com/m-p-esser/unsplash_photo_trends/blob/master/docs/images/Data_Engineering_Git_Branching_Strategy.png):
  - master
  - develop
  - test 

## <a name='Folderstructure'></a>Folder structure

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

## <a name='Mostimportantfilesonrootlevel'></a>Most important files on root level

- `prefect.yaml`: Deployment steps and configuration
- `.pre-commit-config.yaml`: Pre-commit hooks which are run before each commit
- `Makefile`: Settings for Makefile (which are stored in folder `make/*`)
- `pyproject.toml` & `poetry.lock`: Python dependencies 

## <a name='Setup'></a>Setup

### <a name='ActivatePre-commit'></a>Activate Pre-commit 
Install Pre-commit hooks (for code formatting, import statement checks before committing)
- `pre-commit install`

### <a name='EnvironmentVariables'></a>Environment Variables
Define values in `base.env` (not part of this repository)
For reference check `base.env.example` which contains all major variables required for this project

### <a name='GithubActionSecrets'></a>Github Action Secrets
Add the following Secrets as Action secrets to your Github repository: 
- `PREFECT_API_KEY`
- `PREFECT_API_URL`

See https://docs.prefect.io/latest/api-ref/rest-api/#finding-your-prefect-cloud-details

### <a name='GCPSetup'></a>GCP Setup
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

### <a name='EnvironmentSetup'></a>Environment Setup
*necessary everytime you start working on the project*
- `make env-init` to prepare ENV environment variable
- `make dev-init` to setup development environment

### <a name='PrefectSetup'></a>Prefect Setup
As mentioned above, this project requires a Prefect account and access to the Prefect Cloud
- `make setup-prefect` 

### <a name='SetupStorage'></a>Setup Storage
Setup the storage infrastructure by running
- `make create-gcs-buckets`

### <a name='DeploymentandTesting'></a>Deployment and Testing

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