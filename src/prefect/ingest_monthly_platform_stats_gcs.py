""" Flow to request https://api.unsplash.com/stats/month/ Endpoint """

from prefect import flow
from src.prefect.generic_tasks import (
    parse_response,
    request_unsplash_api,
    response_data_to_df,
    store_response_df_to_gcs_bucket,
)
from src.utils import load_env_variables


# Subflow
@flow(retries=3, retry_delay_seconds=10)
def request_monthly_platform_stats() -> list[dict]:
    """Request monthly platform statistics (e.g. number of photos or downloads) from Unsplash API"""

    endpoint = "/stats/month/"
    response = request_unsplash_api(endpoint=endpoint)

    return response


@flow
def ingest_monthly_platform_stats_gcs():
    """Flow to load monthly stats from unsplash and store them in a Google Cloud Storage Bucket"""
    # Call the function with the directory you want to start from

    response = request_monthly_platform_stats()
    response_json = parse_response(response)
    env_variables = load_env_variables()
    env = env_variables["ENV"]  # dev, test or prod

    df = response_data_to_df(response_json, "monthly-platform-stats")
    store_response_df_to_gcs_bucket(df, "monthly-platform-stats", env)


if __name__ == "__main__":
    ingest_monthly_platform_stats_gcs()
