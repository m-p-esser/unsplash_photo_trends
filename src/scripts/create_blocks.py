"""Programmatically create Blocks for Prefect"""

from prefect_gcp import GcpCredentials

from prefect.blocks.system import Secret
from src.utils import load_env_variables

############ Load Env Variables #################

env_variables = load_env_variables()
ENV = env_variables["ENV"]  # dev, test or prod

GCP_PROJECT_ID = env_variables["GCP_PROJECT_ID"]
GCP_DEPLOYMENT_SERVICE_ACCOUNT = env_variables["GCP_DEPLOYMENT_SERVICE_ACCOUNT"]
UNSPLASH_ACCESS_KEY = env_variables["UNSPLASH_ACCESS_KEY"]

############ Google Cloud Platform #################

### GCP Credentials

PREFECT_BLOCK_NAME_GCP_CREDENTIALS = (
    f"{GCP_PROJECT_ID}-{GCP_DEPLOYMENT_SERVICE_ACCOUNT}"
)

with open(f".secrets/deployment_sa_account.json", "r") as f:
    service_account = f.read()

gcp_credentials_block = GcpCredentials(service_account_info=service_account).save(
    PREFECT_BLOCK_NAME_GCP_CREDENTIALS, overwrite=True
)
print(f"Created Block: {gcp_credentials_block}")

########### Secrets #################

### Unsplash API Key

UNSPLASH_ACCESS_KEY_BLOCK_NAME = f"{GCP_PROJECT_ID}-unsplash-access-key"

unsplash_access_key_block = Secret(value=UNSPLASH_ACCESS_KEY).save(
    UNSPLASH_ACCESS_KEY_BLOCK_NAME, overwrite=True
)

print(f"Created Block: {unsplash_access_key_block}")
