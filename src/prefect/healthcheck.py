"""Flow to check health of a machine """

from platform import node, platform

from prefect import flow, get_run_logger


@flow(name="healthcheck")
def healthcheck():
    """Collect information about machine and if it is accessible"""
    logger = get_run_logger()
    logger.info(f"Running on Network '{node()}' and Instance '{platform()}'")

    logger.info("The following modules are available in this flow:")
    logger.info(help("modules"))


if __name__ == "__main__":
    healthcheck()
