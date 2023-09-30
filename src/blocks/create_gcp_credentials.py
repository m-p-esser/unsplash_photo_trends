"""Programmatically create GCP Credential Block for Prefect"""

from prefect_gcp import GcpCredentials

from src.utils import load_env_variables

env_variables = load_env_variables()

PREFECT_BLOCK_NAME_GCP_CREDENTIALS_BLOCK_NAME = f"{env_variables['GCP_PROJECT_ID']}-{env_variables['GCP_DEPLOYMENT_SERVICE_ACCOUNT']}"

with open(f".secrets/deployment_sa_account.json", "r") as f:
    service_account = f.read()

gcp_credentials_block = GcpCredentials(service_account_info=service_account).save(
    name=PREFECT_BLOCK_NAME_GCP_CREDENTIALS_BLOCK_NAME, overwrite=True
)
