"""Programmatically Store ENV variable in form of a String as Prefect Block """

from prefect.blocks.system import String
from src.utils import load_env_variables


def create_env_string_block():
    """Store ENV environment variable as String in Prefect Block"""
    env_variables = load_env_variables()

    ENV = env_variables["ENV"]  # dev, test or prod
    PREFECT_BLOCK_NAME_ENV_STRING = f"{env_variables['GCP_PROJECT_ID']}-{ENV}"

    env_string_block = String(value=ENV).save(
        name=PREFECT_BLOCK_NAME_ENV_STRING, overwrite=True
    )

    return String.load(PREFECT_BLOCK_NAME_ENV_STRING).value


if __name__ == "__main__":
    env = create_env_string_block()
