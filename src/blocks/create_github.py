"""Programmatically create Github Block for Prefect"""

from prefect.filesystems import GitHub
from src.utils import load_env_variables

env_vars = load_env_variables()
ENV = env_vars["ENV"]  # dev, test or prod

branches_mapping = {"dev": "develop", "test": "test", "prod": "master"}
GITHUB_BLOCK_NAME = f"{env_vars['GCP_PROJECT_ID']}-github-{ENV}"

github_block = GitHub(
    repository=f"{env_vars['GITHUB_REPO']}", reference=branches_mapping[ENV]
).save(name=GITHUB_BLOCK_NAME, overwrite=True)
