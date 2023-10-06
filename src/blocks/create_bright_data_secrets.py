"""Programmatically create Bright Data Residential Proxy Secrets (one for User and one for PW) for Prefect"""

from prefect.blocks.system import Secret
from src.utils import load_env_variables

env_vars = load_env_variables()

#### Residential Proxy ######

PREFECT_BLOCK_NAME_BRIGHT_DATA_RESIDENTIAL_PROXY = (
    f"{env_vars['GCP_PROJECT_ID']}-bright-data-residential-proxy-username"
)

gcp_credentials_block = Secret(
    value=env_vars["BRIGHT_DATA_RESIDENTAL_PROXY_USERNAME"]
).save(name=PREFECT_BLOCK_NAME_BRIGHT_DATA_RESIDENTIAL_PROXY, overwrite=True)

PREFECT_BLOCK_NAME_BRIGHT_DATA_RESIDENTIAL_PROXY = (
    f"{env_vars['GCP_PROJECT_ID']}-bright-data-residential-proxy-password"
)

gcp_credentials_block = Secret(
    value=env_vars["BRIGHT_DATA_RESIDENTAL_PROXY_PASSWORD"]
).save(name=PREFECT_BLOCK_NAME_BRIGHT_DATA_RESIDENTIAL_PROXY, overwrite=True)

#### Datacenter Proxy ######

PREFECT_BLOCK_NAME_BRIGHT_DATA_DATACENTER_PROXY = (
    f"{env_vars['GCP_PROJECT_ID']}-bright-data-datacenter-proxy-username"
)

gcp_credentials_block = Secret(
    value=env_vars["BRIGHT_DATA_DATACENTER_PROXY_USERNAME"]
).save(name=PREFECT_BLOCK_NAME_BRIGHT_DATA_DATACENTER_PROXY, overwrite=True)

PREFECT_BLOCK_NAME_BRIGHT_DATA_DATACENTER_PROXY = (
    f"{env_vars['GCP_PROJECT_ID']}-bright-data-datacenter-proxy-password"
)

gcp_credentials_block = Secret(
    value=env_vars["BRIGHT_DATA_DATACENTER_PROXY_PASSWORD"]
).save(name=PREFECT_BLOCK_NAME_BRIGHT_DATA_DATACENTER_PROXY, overwrite=True)
