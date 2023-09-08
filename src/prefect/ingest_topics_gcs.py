""" Flow to request https://api.unsplash.com/topics/ Endpoint """

import datetime
import json
from tempfile import NamedTemporaryFile

import requests
from google.cloud import storage

from etl.load import upload_blob_from_file
from prefect import flow, get_run_logger, task
from prefect.blocks.system import Secret
from utils import load_env_variables, timer


@task
@timer
def request_topics() -> list[dict]:
    """Request topics (= photography genres which have a seperate content site on unsplash) from Unsplash API"""
    logger = get_run_logger()

    UNSPLASH_ACCESS_KEY = Secret.load("unsplash-photo-trends-unsplash-access-key").get()
    BASE_URL = "https://api.unsplash.com"
    URI = BASE_URL + "/topics/"

    logger.info(f"Requesting endpoint: {URI}")
    response = requests.get(
        url=URI, params={"client_id": UNSPLASH_ACCESS_KEY, "per_page": 30}
    )

    response.raise_for_status()

    rate_limit_limit = int(response.headers["X-Ratelimit-Limit"])
    rate_limit_remaining = int(response.headers["X-Ratelimit-Remaining"])
    consumed_quota = (rate_limit_limit - rate_limit_remaining) / rate_limit_limit

    if consumed_quota > 0.8:
        logger.warning(
            f"Rate limit almost reached: {consumed_quota}%% of Quota consumed."
        )

    if rate_limit_remaining == 0:
        logger.error(
            f"Rate limit reached: {consumed_quota}%% of Quota consumed. Wait to continue"
        )

    response_json = response.json()
    logger.info(f"Response contains data for {len(response_json)} topics")

    return response_json


@task
@timer
def load_topics_as_jsonl_to_gcs_bucket(
    response_json: dict, env: str = "DEV"
) -> storage.bucket.Bucket.blob:
    """Store topics (= photography genres which have a seperate content site on unsplash) as Blob in Google Cloud Storage Bucket"""
    logger = get_run_logger()

    with NamedTemporaryFile(delete=True, suffix=".jsonl") as temp_file:
        logger.info(f"Writing topics data to file {temp_file.name}")
        for topic in response_json:
            topic_string = json.dumps(topic) + "\n"
            temp_file.write(topic_string.encode())

        today = datetime.date.today().strftime("%Y%m%d")
        blob_name = f"topics_{today}.jsonl"

        blob = upload_blob_from_file(
            bucket_name=f"unsplash-topics-{env}",
            source_file_name=temp_file.name,
            destination_blob_name=blob_name,
            gcp_credential_block_name="unsplash-photo-trends-deployment-sa",
        )
        logger.info(f"Uploaded topics data to {blob}")

        return blob


@flow
@timer
def ingest_topics_gcs():
    """Flow to load topics from Unsplash and store them in a Google Cloud Storage Bucket"""
    response_json = request_topics()
    env_variables = load_env_variables()
    env = env_variables["ENV"]  # dev, test or prod
    load_topics_as_jsonl_to_gcs_bucket(response_json, env)


if __name__ == "__main__":
    ingest_topics_gcs()