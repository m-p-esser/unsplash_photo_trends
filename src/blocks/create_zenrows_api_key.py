"""Programmatically create Zenrows API Key for Prefect"""

from prefect.blocks.system import Secret
from src.utils import load_env_variables

env_vars = load_env_variables()

ZENROWS_API_KEY_BLOCK_NAME = f"{env_vars['GCP_PROJECT_ID']}-zenrows-api-key"

unsplash_access_key_block = Secret(value=env_vars["ZENROWS_API_KEY"]).save(
    name=ZENROWS_API_KEY_BLOCK_NAME, overwrite=True
)
