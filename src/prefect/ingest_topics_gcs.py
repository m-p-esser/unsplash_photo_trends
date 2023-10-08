""" Flow to request https://api.unsplash.com/topics/ Endpoint """

from prefect import flow
from src.prefect.generic_tasks import (
    parse_response,
    request_unsplash_api,
    response_data_to_df,
    store_response_df_to_gcs_bucket,
)
from src.utils import load_env_variables, timer


# Subflow
@flow(retries=3, retry_delay_seconds=10)
@timer
def request_topics() -> list[dict]:
    """Request topics (= photography genres which have a seperate content site on unsplash) from Unsplash API"""

    endpoint = "/topics/"
    response = request_unsplash_api(endpoint)

    return response


@flow
@timer
def ingest_topics_gcs():
    """Flow to load topics from Unsplash and store them in a Google Cloud Storage Bucket"""
    # Call the function with the directory you want to start from

    response = request_topics()
    response_json = parse_response(response)
    env_variables = load_env_variables()
    env = env_variables["ENV"]  # dev, test or prod

    df = response_data_to_df(response_json, "topics")
    store_response_df_to_gcs_bucket(df, "topics", env)


if __name__ == "__main__":
    ingest_topics_gcs()
