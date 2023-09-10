""" Flow to request https://api.unsplash.com/topics/ Endpoint """

import datetime
import json
from tempfile import NamedTemporaryFile

import pandas as pd
from google.cloud import storage

from prefect import flow, get_run_logger, task
from src.etl.extract import request_unsplash
from src.etl.load import upload_blob_from_file
from src.utils import load_env_variables, timer


@task(retries=3, retry_delay_seconds=10)
@timer
def request_topics() -> list[dict]:
    """Request topics (= photography genres which have a seperate content site on unsplash) from Unsplash API"""

    endpoint = "/topics/"
    response_json = request_unsplash(endpoint)

    return response_json


@task(retries=3, retry_delay_seconds=10)
@timer
def load_topics_to_gcs_bucket(
    response_json: dict, env: str = "dev"
) -> storage.blob.Blob:
    """Store topics (= photography genres which have a seperate content site on unsplash) as Blob in Google Cloud Storage Bucket"""
    logger = get_run_logger()

    with NamedTemporaryFile(delete=True, suffix=".jsonl") as temp_jsonl:
        logger.info(f"Writing topics data to file {temp_jsonl.name}")
        for topic in response_json:
            topic_string = json.dumps(topic) + "\n"
            temp_jsonl.write(topic_string.encode())

        df = pd.read_json(temp_jsonl.name, lines=True)
        df["requested_data_at"] = datetime.datetime.now()
        logger.info(
            f"The Parquet file contains {df.shape[1]} columns and {df.shape[0]} rows"
        )

        with NamedTemporaryFile(delete=True, suffix=".parquet") as temp_parquet:
            df.to_parquet(temp_parquet.name)

            today = datetime.date.today().strftime("%Y%m%d")
            blob_name = f"topics_{today}.parquet"

            blob = upload_blob_from_file(
                bucket_name=f"unsplash-topics-{env}",
                source_file_name=temp_parquet.name,
                destination_blob_name=blob_name,
                gcp_credential_block_name="unsplash-photo-trends-deployment-sa",
            )
            logger.info(f"Uploaded topics data to {blob}")

        return blob


@flow
@timer
def ingest_topics_gcs():
    """Flow to load topics from Unsplash and store them in a Google Cloud Storage Bucket"""
    # Call the function with the directory you want to start from

    response_json = request_topics()
    env_variables = load_env_variables()
    env = env_variables["ENV"]  # dev, test or prod
    load_topics_to_gcs_bucket(response_json, env)


if __name__ == "__main__":
    ingest_topics_gcs()
