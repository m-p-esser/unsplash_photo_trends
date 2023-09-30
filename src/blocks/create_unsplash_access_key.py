"""Programmatically create Unsplash Access Key Secret Block for Prefect"""

from prefect.blocks.system import Secret
from src.utils import load_env_variables

env_vars = load_env_variables()

UNSPLASH_ACCESS_KEY_BLOCK_NAME = f"{env_vars['GCP_PROJECT_ID']}-unsplash-access-key"

unsplash_access_key_block = Secret(value=env_vars["UNSPLASH_ACCESS_KEY"]).save(
    name=UNSPLASH_ACCESS_KEY_BLOCK_NAME, overwrite=True
)
