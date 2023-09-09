"""Flow to check health of a machine """

from importlib.metadata import distributions
from platform import node, platform, python_version

from prefect import flow, get_run_logger


@flow(name="healthcheck")
def healthcheck():
    """Collect information about machine and if it is accessible"""
    logger = get_run_logger()
    logger.info(f"Running on Network '{node()}' and Instance '{platform()}'")
    logger.info(f"Running on Python Version '{python_version()}'")

    logger.info("The following modules are available in this flow:")
    for dist in distributions():
        logger.info(f"{dist.metadata['Name']}=={dist.version}")


if __name__ == "__main__":
    healthcheck()
