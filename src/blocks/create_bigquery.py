"""Programmatically create GCP Bigquery Block for Prefect"""

from prefect_gcp import BigQueryWarehouse, GcpCredentials

from src.utils import load_env_variables

env_variables = load_env_variables()

ENV = env_variables["ENV"]  # dev, test or prod
PREFECT_BLOCK_NAME_GCP_CREDENTIALS = f"{env_variables['GCP_PROJECT_ID']}-{env_variables['GCP_DEPLOYMENT_SERVICE_ACCOUNT']}"
GOOGLE_BIGQUERY_BLOCK_NAME = f"{env_variables['GCP_PROJECT_ID']}-bigquery"

bigquery_block = BigQueryWarehouse(
    gcp_credentials=GcpCredentials.load(PREFECT_BLOCK_NAME_GCP_CREDENTIALS),
    fetch_size=100,
).save(name=GOOGLE_BIGQUERY_BLOCK_NAME, overwrite=True)
