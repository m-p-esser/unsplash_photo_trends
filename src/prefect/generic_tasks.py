""" Collection of generic tasks that can be reused across flows """

import datetime
import json
import math
from tempfile import NamedTemporaryFile

import pandas as pd
import requests
from google.cloud import storage

from prefect import get_run_logger, task
from prefect.blocks.system import Secret
from src.etl.load import upload_blob_from_file
from src.utils import timer


@task(retries=3, retry_delay_seconds=10)
@timer
def request_unsplash(
    endpoint: str, params: dict = {"per_page": 30}
) -> requests.Response:
    """Request data from Unsplash API"""
    logger = get_run_logger()

    params["client_id"] = Secret.load("unsplash-photo-trends-unsplash-access-key").get()
    BASE_URL = "https://api.unsplash.com"
    URI = BASE_URL + endpoint

    logger.info(f"Requesting endpoint: {URI}")
    response = requests.get(url=URI, params=params)

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

    return response


@task(retries=3, retry_delay_seconds=10)
@timer
def parse_response(response: requests.Response) -> dict:
    """Convert Response to Dict"""
    logger = get_run_logger()

    response_json = response.json()

    logger.info(
        f"Response contains data for {len(response_json)} entries (rows or columns)"
    )

    return response_json


@task(retries=3, retry_delay_seconds=10)
@timer
def response_data_to_df(response_json: dict, response_data_name: str) -> pd.DataFrame:
    """Store Response data as in Dataframe"""

    logger = get_run_logger()

    with NamedTemporaryFile(delete=True, suffix=".jsonl") as temp_file:
        logger.info(f"Writing {response_data_name} data to file {temp_file.name}")

        if isinstance(response_json, list):
            if isinstance(response_json[0], dict):
                for item in response_json:
                    item_string = json.dumps(item) + "\n"
                    temp_file.write(item_string.encode())

                df = pd.read_json(temp_file.name, lines=True)

        elif isinstance(response_json, dict):
            data = {
                k: [v] for k, v in response_json.items()
            }  # Dataframe expects {'key1': ['value1], 'key2': ['value2]}
            df = pd.DataFrame(data)

        else:
            raise ValueError(f"No parsing method for {type(response_json)} implemented")

        df["requested_data_at"] = datetime.datetime.now()
        logger.info(
            f"The Dataframe contains {df.shape[1]} columns and {df.shape[0]} rows"
        )

    return df


@task(retries=3, retry_delay_seconds=10)
@timer
def store_response_df_to_gcs_bucket(
    df: pd.DataFrame, response_data_name: str, env: str = "dev"
) -> storage.blob.Blob:
    """Store Dataframe as Blob in Google Cloud Storage Bucket"""
    logger = get_run_logger()

    with NamedTemporaryFile(delete=True, suffix=".parquet") as temp_parquet:
        df.to_parquet(temp_parquet.name)

        today = datetime.date.today().strftime("%Y%m%d")
        blob_name = f"{response_data_name}_{today}.parquet"
        blob = upload_blob_from_file(
            bucket_name=f"unsplash-{response_data_name}-{env}",
            source_file_name=temp_parquet.name,
            destination_blob_name=blob_name,
            gcp_credential_block_name="unsplash-photo-trends-deployment-sa",
        )

        logger.info(f"Uploaded topics data to {blob}")

        return blob


@task(retries=3, retry_delay_seconds=10)
@timer
def count_number_stored_files_in_gcs_bucket(storage_client, bucket_name: str) -> int:
    """Count the number of files / blobs stored in Google Cloud Storage Bucket"""

    logger = get_run_logger()

    bucket = storage_client.get_bucket(bucket_name)
    blobs = bucket.list_blobs()
    number_stored_files = sum(1 for _ in blobs)

    logger.info(f"Number of files in '{bucket.name}': {number_stored_files}")

    return int(number_stored_files)


@task(retries=3, retry_delay_seconds=10)
@timer
def get_processing_progress_from_response_header(
    response, number_stored_photos: int
) -> dict:
    """Use Response header data to calculate how many pages/objects have been processed
    and how many pages/objects still need to be processed"""

    logger = get_run_logger()

    number_requestable_objects = int(response.headers["X-Total"])
    number_objects_per_page = int(response.headers["X-Per-Page"])
    last_page_number = math.ceil(number_requestable_objects / number_objects_per_page)
    remaining_number_objects_to_request = (
        number_requestable_objects - number_stored_photos
    )
    number_processed_pages = math.floor(number_stored_photos / number_objects_per_page)

    processing_progress = {
        "number_requestable_objects": number_requestable_objects,
        "number_objects_per_page": number_objects_per_page,
        "last_page_number": last_page_number,
        "remaining_number_objects_to_request": remaining_number_objects_to_request,
        "number_processed_pages": number_processed_pages,
    }

    logger.info(processing_progress)

    return processing_progress
