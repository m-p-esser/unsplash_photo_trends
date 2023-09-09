""" Sync Google Cloud Storage (JSONL) with Bigquery. PUSH Pattern that needs to be setup just for once for each Bigquery Table """

from google.cloud import bigquery
from google.cloud.exceptions import NotFound
from prefect_gcp import GcpCredentials

from prefect import flow, get_run_logger, task
from src.utils import load_env_variables, timer


@task
@timer
def construct_bigquery_client() -> bigquery.client.Client:
    """Create Authenticated Bigquery Client"""

    logger = get_run_logger()

    gcp_credentials = GcpCredentials.load("unsplash-photo-trends-deployment-sa")
    project = gcp_credentials.project
    bigquery_client = gcp_credentials.get_bigquery_client(
        project=project, location="europe-west3"
    )

    logger.info(f"Created Bigquery Client: {bigquery_client}")

    return bigquery_client


@task
@timer
def create_dataset(bigquery_client: bigquery.client.Client, env: str = "dev"):
    """Create Bigquery Dataset"""
    logger = get_run_logger()

    dataset_reference = bigquery.DatasetReference(
        project=bigquery_client.project, dataset_id=env
    )
    try:
        bigquery_client.get_dataset(dataset_reference)
        logger.info(f"Dataset {dataset_reference} already exists")
        dataset_exists = True
    except NotFound:
        dataset_exists = False
        logger.info(f"Dataset {dataset_reference} is not found")

    if not dataset_exists:
        bigquery_client.create_dataset(dataset_reference)
        logger.info(f"Created dataset '{dataset_reference}'")


@task
@timer
def sync_gcs_and_bigquery_table(
    bigquery_client: bigquery.client.Client,
    table_name: str,
    source_uri: str,
    env: str = "dev",
    file_format: str = "PARQUET",
):
    """Sync Google Cloud Storage with Bigquery table using Push pattern

    Example for `source_uri`: "gs://unsplash-topics-dev/*.parquet"

    """
    logger = get_run_logger()

    dataset_reference = bigquery.DatasetReference(
        project=bigquery_client.project,
        dataset_id=env,
    )

    table_reference = bigquery.TableReference(
        dataset_ref=dataset_reference, table_id=table_name
    )

    table = bigquery.Table(table_ref=table_reference)

    external_config = bigquery.ExternalConfig(file_format)
    external_config.source_uris = [source_uri]
    table.external_data_configuration = external_config

    # Create a permanent table linked to the GCS file
    table = bigquery_client.create_table(table)
    logger.info(f"Synced Bigquery table '{table}' with '{source_uri}'")


@flow
@timer
def sync_topics_gcs_to_bigquery(table_name: str, source_uri: str, file_format: str):
    """Sync Google Cloud Storage with Bigquery Table using Push pattern"""
    bigquery_client = construct_bigquery_client()

    env_variables = load_env_variables()
    env = env_variables["ENV"]  # dev, test or prod

    create_dataset(bigquery_client, env)
    sync_gcs_and_bigquery_table(
        bigquery_client,
        table_name,
        source_uri,
        env,
        file_format,
    )


if __name__ == "__main__":
    sync_topics_gcs_to_bigquery(
        table_name="topics",
        source_uri="gs://unsplash-topics-dev/*.parquet",
        file_format="PARQUET",
    )
