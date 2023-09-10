""" Collection of Extraction functions """

########## GCP ##############

import requests
from google.cloud import storage
from prefect_gcp import GcpCredentials

from prefect import get_run_logger
from prefect.blocks.system import Secret


def download_blob_to_file(
    bucket_name: str,
    source_blob_name: str,
    destination_file_name: str,
    gcp_credential_block_name: str,
) -> storage.bucket.Bucket.blob:
    """Downloads a blob from the bucket."""

    gcp_credentials = GcpCredentials.load(gcp_credential_block_name)
    storage_client = gcp_credentials.get_cloud_storage_client()

    bucket = storage_client.bucket(bucket_name)

    # Construct a client side representation of a blob.
    # Note `Bucket.blob` differs from `Bucket.get_blob` as it doesn't retrieve
    # any content from Google Cloud Storage. As we don't need additional data,
    # using `Bucket.blob` is preferred here.
    blob = bucket.blob(source_blob_name)
    blob.download_to_filename(destination_file_name)

    return blob


def download_blob_into_memory(
    bucket_name: str, blob_name: str, gcp_credential_block_name: str
) -> str:
    """Downloads a blob into memory."""

    gcp_credentials = GcpCredentials.load(gcp_credential_block_name)
    storage_client = gcp_credentials.get_cloud_storage_client()

    bucket = storage_client.bucket(bucket_name)

    # Construct a client side representation of a blob.
    # Note `Bucket.blob` differs from `Bucket.get_blob` as it doesn't retrieve
    # any content from Google Cloud Storage. As we don't need additional data,
    # using `Bucket.blob` is preferred here.
    blob = bucket.blob(blob_name)
    contents = blob.download_as_string()

    return contents


########## Request ##############


def request_unsplash(endpoint: str) -> list[dict]:
    """Request data from Unsplash API"""
    logger = get_run_logger()

    UNSPLASH_ACCESS_KEY = Secret.load("unsplash-photo-trends-unsplash-access-key").get()
    BASE_URL = "https://api.unsplash.com"
    URI = BASE_URL + endpoint

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
