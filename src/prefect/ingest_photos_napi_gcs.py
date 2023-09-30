""" Flow to request https://unsplash.com/napi/photos Endpoint (Backend API)"""

import json
import math
import time
from datetime import timedelta
from pprint import pformat
from random import randint

from google.cloud import storage
from prefect_gcp.bigquery import bigquery_query
from prefect_gcp.credentials import GcpCredentials

from prefect import flow, get_run_logger, task
from prefect.blocks.system import Secret
from prefect.task_runners import ConcurrentTaskRunner
from prefect.tasks import task_input_hash
from src.etl.load import upload_blob_from_memory
from src.prefect.generic_tasks import (
    parse_response,
    request_unsplash,
    request_unsplash_napi,
)
from src.utils import load_env_variables, timer


@flow(retries=3, retry_delay_seconds=10)  # Subflow (2nd level)
def request_first_page(
    params: dict = {"per_page": 30, "page": 1, "order_by": "oldest"}
):
    """Request first page of https://api.unsplash.com/photos Endpoint"""

    logger = get_run_logger()
    logger.info(f"Requesting page number 1 of https://api.unsplash.com/photos endpoint")

    response = request_unsplash("/photos", params)

    return response


@flow(retries=3, retry_delay_seconds=10)  # Subflow (2nd level)
@timer
def request_photos_napi(params: dict, zenrows_api_key: str):
    """Request topics (= photography genres which have a seperate content site on unsplash) from Unsplash API"""

    endpoint = "/photos"
    response = request_unsplash_napi(endpoint, params, zenrows_api_key)

    return response


@task(
    retries=3,
    retry_delay_seconds=3,
    cache_key_fn=task_input_hash,
    cache_expiration=timedelta(hours=1),
)  # Task (3rd level)
def _upload_photo_metadata_as_blob(
    response,
    photo_metadata: dict,
    gcp_credential_block_name: str,
    bucket_name: str,
) -> storage.blob.Blob:
    """Upload single photo metadata as blob to Google Cloud Storage Bucket"""

    logger = get_run_logger()

    photo = {
        "payload": photo_metadata,
        "request_metadata": {
            "requested_at": response.headers["Zr-Date"],
            "request_id": response.headers["X-Request-Id"],
            "request_url": response.headers["Zr-Final-Url"],
        },
    }

    photo_id = photo["payload"]["id"]
    blob_name = f"{photo_id}.json"
    bytes = json.dumps(photo).encode("utf-8")

    logger.info(f"Uploading '{blob_name}' to {bucket_name}")
    upload_blob_from_memory(bucket_name, bytes, blob_name, gcp_credential_block_name)


@flow(
    retries=3,
    retry_delay_seconds=10,
    timeout_seconds=120,
    task_runner=ConcurrentTaskRunner(),
)  # Subflow (2nd level)
@timer
def upload_photo_metadata_to_gcs(
    response,
    response_json: list[dict],
    gcp_credential_block_name: str,
    bucket_name: str,
):
    """Asychronously upload photo metadata as blob to Google Cloud Storage Bucket"""

    for photo_metadata in response_json:
        _upload_photo_metadata_as_blob.submit(
            response, photo_metadata, gcp_credential_block_name, bucket_name
        )


@flow(
    retries=3,
    retry_delay_seconds=10,
)  # Subflow (2nd level)
def get_last_requested_page_from_logs(
    gcp_credentials: GcpCredentials, env: str = "dev", location="europe-west3"
) -> int:
    """Get last requested page where photo metadata has been stored"""

    query = f"""
            SELECT MAX(requested_page) as last_requested_page
            FROM `unsplash-photo-trends.{env}.photos-editorial-metadata-request-log`
        """

    result = bigquery_query(query, gcp_credentials, location=location)

    last_requested_page = result[0][0]  # First Row and Column

    if last_requested_page is None:
        last_requested_page = 0

    return last_requested_page


@flow(
    retries=3,
    retry_delay_seconds=10,
)  # Subflow (2nd level)
def write_request_log_to_bigquery(
    gcp_credentials: GcpCredentials,
    request_id: str,
    request_url: str,
    params: dict,
    env: str = "dev",
    location="europe-west3",
):
    """Write for which URLs metadata has been requested and stored in Google Cloud Storage"""

    logger = get_run_logger()
    logger.info(f"Unsplash Request ID: {request_id}")

    location = "europe-west3"

    query = f"""
        SELECT *
            FROM `unsplash-photo-trends.{env}.photos-editorial-metadata-request-log`
            WHERE request_url = @request_url
        """

    query_params = [("request_url", "STRING", request_url)]

    row = bigquery_query(query, gcp_credentials, query_params, location=location)

    if len(row) > 0:
        query = f"""
            UPDATE `unsplash-photo-trends.{env}.photos-editorial-metadata-request-log`
            SET last_requested_at = CURRENT_DATETIME(), request_id = @request_id
            WHERE request_url = @request_url
        """

        query_params = [
            ("request_url", "STRING", request_url),
            ("request_id", "STRING", request_id),
        ]

        bigquery_query(query, gcp_credentials, query_params, location=location)

        logger.info(f"Updated existing log entry for Request URL: {request_url}")

    if len(row) == 0:
        query = f"""
            INSERT `unsplash-photo-trends.{env}.photos-editorial-metadata-request-log`
            (request_id, request_url, requested_page, number_requested_objects_in_payload, first_requested_at, last_requested_at)
            VALUES (@request_id, @request_url, @requested_page, @per_page, CURRENT_DATETIME(), CURRENT_DATETIME())
        """

        query_params = [
            ("request_url", "STRING", request_url),
            ("request_id", "STRING", request_id),
            ("requested_page", "INT64", params["page"]),
            ("per_page", "INT64", params["per_page"]),
        ]

        bigquery_query(query, gcp_credentials, query_params, location=location)

        logger.info(f"Add new log entry for Request URL: {request_url}")

    else:
        raise ValueError(
            f"{row} seems to be malformed. Can't insert or update logs based on this data"
        )


@flow  # Main Flow (1st level)
@timer
def ingest_photos_napi_gcs(
    gcp_credential_block_name: str,
    zen_rows_api_key_block_name: str,
    params: dict,
):
    """Flow to load Editorial photos from Unsplash and store them in a Google Cloud Storage Bucket"""

    logger = get_run_logger()

    # Init all variables
    env_variables = load_env_variables()
    env = env_variables["ENV"]  # dev, test or prod
    bucket_name = f"photos-editorial-metadata-{env}"

    # Init all secrets and credentials
    gcp_credentials = GcpCredentials.load(gcp_credential_block_name)
    zen_rows_api_key = Secret.load(zen_rows_api_key_block_name).get()

    # Request first page
    first_page_response = request_first_page()
    number_requestable_objects = int(first_page_response.headers["X-Total"])
    number_objects_per_page = int(first_page_response.headers["X-Per-Page"])
    total_number_pages = math.ceil(number_requestable_objects / number_objects_per_page)
    log_dict = {
        "Number of Requestable Objects": number_requestable_objects,
        "Number of Objects per Page": number_objects_per_page,
        "Total number of pages": total_number_pages,
    }
    logger.info(f"The endpoint contains: \n {pformat(log_dict)}")

    # Get last requested page from Unsplash photo endpoint
    last_requested_page = get_last_requested_page_from_logs(gcp_credentials, env)
    logger.info(f"The last requested page number is: {last_requested_page}")

    # Counter
    total_number_pages = 2  # just for testing
    next_page = last_requested_page + 1
    number_stored_images = 0

    # Extend Params
    params["page"] = next_page
    params["order_by"] = "oldest"

    while next_page <= total_number_pages:
        time.sleep(randint(1, 3))
        response = request_photos_napi(params, zen_rows_api_key)
        logger.info(f"Response headers: \n {response.headers}")
        response_json = parse_response(response)

        # Asychronously collect data
        upload_photo_metadata_to_gcs(
            response, response_json, gcp_credential_block_name, bucket_name
        )
        logger.info(
            f"Uploaded {len(response_json)} blobs to Google Cloud Storage Bucket: {bucket_name}"
        )

        number_stored_images += params["per_page"]
        logger.info(
            f"Number of stored images in this data collection run: {number_stored_images}"
        )

        request_id = response.headers["X-Request-Id"]
        request_url = response.headers["Zr-Final-Url"]
        write_request_log_to_bigquery(gcp_credentials, request_id, request_url, params)

        # Break the Loop if 450 images have been collected to avoid "OSError: [Errno 24] Too many open files"
        if number_stored_images == 450:
            logger.info(
                "Downloaded metadata for 450 Editorial images of Unsplash platform"
            )
            break

        next_page += 1


if __name__ == "__main__":
    ingest_photos_napi_gcs(
        gcp_credential_block_name="unsplash-photo-trends-deployment-sa",
        zen_rows_api_key_block_name="unsplash-photo-trends-zenrows-api-key",
        params={"per_page": 30},
    )
