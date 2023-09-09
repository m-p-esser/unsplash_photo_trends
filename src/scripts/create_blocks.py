"""Programmatically create Blocks for Prefect"""

from prefect_gcp import GcpCredentials
from prefect_gcp.bigquery import BigQueryWarehouse
from prefect_gcp.cloud_run import CloudRunJob

from prefect.blocks.system import Secret
from prefect.filesystems import GitHub
from src.utils import load_env_variables

############ Google Cloud Platform #################

### GCP Credentials


def create_gcp_credentials_block():
    """Create GCP Credentials Block"""
    env_variables = load_env_variables()

    PREFECT_BLOCK_NAME_GCP_CREDENTIALS_BLOCK_NAME = f"{env_variables['GCP_PROJECT_ID']}-{env_variables['GCP_DEPLOYMENT_SERVICE_ACCOUNT']}"

    with open(f".secrets/deployment_sa_account.json", "r") as f:
        service_account = f.read()

    gcp_credentials_block = GcpCredentials(service_account_info=service_account).save(
        name=PREFECT_BLOCK_NAME_GCP_CREDENTIALS_BLOCK_NAME, overwrite=True
    )
    print(f"Created GCP Credentials Block: {gcp_credentials_block}")


### Google Bigquery


def create_bigquery_block():
    """Create Google Bigquery Block"""

    env_vars = load_env_variables()

    ENV = env_vars["ENV"]  # dev, test or prod
    PREFECT_BLOCK_NAME_GCP_CREDENTIALS = (
        f"{env_vars['GCP_PROJECT_ID']}-{env_vars['GCP_DEPLOYMENT_SERVICE_ACCOUNT']}"
    )
    GOOGLE_BIGQUERY_BLOCK_NAME = f"{env_vars['GCP_PROJECT_ID']}-bigquery-{ENV}"

    bigquery_block = BigQueryWarehouse(
        gcp_credentials=GcpCredentials.load(PREFECT_BLOCK_NAME_GCP_CREDENTIALS)
    ).save(name=GOOGLE_BIGQUERY_BLOCK_NAME, overwrite=True)

    print(f"Created Bigquery Block: {bigquery_block}")


### Google Cloud Run


def create_google_cloud_run_block():
    """Create a Generic Cloud Run Block that can be reused across Flows"""

    env_vars = load_env_variables()
    ENV = env_vars["ENV"]  # dev, test or prod

    GCP_CREDENTIALS_PREFECT_BLOCK_NAME = (
        f"{env_vars['GCP_PROJECT_ID']}-{env_vars['GCP_DEPLOYMENT_SERVICE_ACCOUNT']}"
    )
    GOOGLE_CLOUD_RUN_BLOCK_NAME = f"{env_vars['GCP_PROJECT_ID']}-google-cloud-run-{ENV}"

    gcp_credentials = GcpCredentials.load(GCP_CREDENTIALS_PREFECT_BLOCK_NAME)
    project_id = gcp_credentials.project
    registry_adress = (
        f"{env_vars['GCP_DEFAULT_REGION']}-docker.pkg.dev/{project_id}/prefect-{ENV}"
    )

    cloud_run_job_block = CloudRunJob(
        credentials=gcp_credentials,
        project_id=project_id,
        image=f"{registry_adress}/prefect:{env_vars['PREFECT_VERSION']}-python{env_vars['PYTHON_VERSION']}",
        region=env_vars["GCP_DEFAULT_REGION"],
    ).save(name=GOOGLE_CLOUD_RUN_BLOCK_NAME, overwrite=True)

    print(f"Created Cloud Run Block: {cloud_run_job_block}")


########### Secrets #################


### Unsplash API Key


def create_unsplash_access_key_block():
    """Create Unsplash Access Key Block"""
    env_vars = load_env_variables()

    UNSPLASH_ACCESS_KEY_BLOCK_NAME = f"{env_vars['GCP_PROJECT_ID']}-unsplash-access-key"

    unsplash_access_key_block = Secret(value=env_vars["UNSPLASH_ACCESS_KEY"]).save(
        name=UNSPLASH_ACCESS_KEY_BLOCK_NAME, overwrite=True
    )

    print(f"Created Unsplash Block: {unsplash_access_key_block}")


############ Github #################


def create_github_block():
    """Create Github Block"""

    env_vars = load_env_variables()
    ENV = env_vars["ENV"]  # dev, test or prod

    branches_mapping = {"dev": "develop", "test": "test", "prod": "master"}
    GITHUB_BLOCK_NAME = f"{env_vars['GCP_PROJECT_ID']}-github-{ENV}"

    github_block = GitHub(
        repository=f"{env_vars['GITHUB_REPO']}", reference=branches_mapping[ENV]
    ).save(name=GITHUB_BLOCK_NAME, overwrite=True)

    print(f"Created Github Block: {github_block}")


if __name__ == "__main__":
    create_gcp_credentials_block()
    create_unsplash_access_key_block()
    create_google_cloud_run_block()
    create_github_block()
    create_bigquery_block()
