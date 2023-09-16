""" Flow to request https://api.unsplash.com/photos Endpoint """

import json
import math
from datetime import timedelta

from google.cloud import storage
from prefect_gcp.credentials import GcpCredentials

from prefect import flow, get_run_logger, task
from prefect.task_runners import ConcurrentTaskRunner
from prefect.tasks import task_input_hash
from src.etl.load import upload_blob_from_memory
from src.prefect.generic_tasks import (
    count_number_stored_files_in_gcs_bucket,
    get_processing_progress_from_response_header,
    parse_response,
    request_unsplash,
)
from src.utils import load_env_variables, timer


@flow(retries=3, retry_delay_seconds=10)  # Subflow (2nd level)
@timer
def request_photos(params: dict):
    """Request topics (= photography genres which have a seperate content site on unsplash) from Unsplash API"""

    endpoint = "/photos"
    response = request_unsplash(endpoint, params)

    return response


@flow(retries=3, retry_delay_seconds=10)  # Subflow (2nd level)
def request_first_page(
    params: dict = {"per_page": 30, "page": 1, "order_by": "oldest"}
):
    """Request first page of https://api.unsplash.com/photos Endpoint
    IMPORTANT: 'per_page' needs to stay fixed on 30, otherwise the algorithm doesn't work
    """

    logger = get_run_logger()
    logger.info(f"Requesting page number 1 of https://api.unsplash.com/photos endpoint")

    if params["per_page"] != 30:
        raise ValueError(
            "`per_page` parameter needs to be 30 for the main flow to work"
        )

    response = request_photos(params)

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
    page_number: int,
) -> storage.blob.Blob:
    """Upload single photo metadata as blob to Google Cloud Storage Bucket"""

    photo = {
        "payload": photo_metadata,
        "request_metadata": {
            "total_pages": response.headers["X-Total"],
            "last_page_number": math.ceil(
                int(response.headers["X-Total"]) / int(response.headers["X-Per-Page"])
            ),
            "requested_at": response.headers["Date"],
            "request_id": response.headers["X-Request-Id"],
            "requested_page": page_number,
        },
    }

    photo_id = photo["payload"]["id"]
    blob_name = f"{photo_id}.json"
    bytes = json.dumps(photo).encode("utf-8")
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
    page_counter: int,
):
    """Asychronously upload photo metadata as blob to Google Cloud Storage Bucket"""

    get_run_logger()

    for photo_metadata in response_json:
        _upload_photo_metadata_as_blob.submit(
            response,
            photo_metadata,
            gcp_credential_block_name,
            bucket_name,
            page_counter,
        )


@flow  # Main Flow (1st level)
@timer
def ingest_photos_gcs(gcp_credential_block_name: str):
    """Flow to load Editorial photos from Unsplash and store them in a Google Cloud Storage Bucket"""

    logger = get_run_logger()

    # Init all variables and clients
    env_variables = load_env_variables()
    env = env_variables["ENV"]  # dev, test or prod
    gcp_credentials = GcpCredentials.load(gcp_credential_block_name)
    storage_client = gcp_credentials.get_cloud_storage_client()
    bucket_name = f"photos-editorial-metadata-{env}"

    # Run Subflows
    number_stored_photos = count_number_stored_files_in_gcs_bucket(
        storage_client, bucket_name
    )

    first_page_response = request_first_page()
    processing_progress = get_processing_progress_from_response_header(
        first_page_response, number_stored_photos
    )

    start_page_number = processing_progress["number_processed_pages"] + 1
    last_page_number = processing_progress["last_page_number"]

    page_counter = start_page_number
    number_new_stored_images = 0

    while True:
        # Request single page of endpoint
        params = {
            "per_page": 30,
            "page": page_counter,
            "order_by": "oldest",
        }  # 'per_page' needs to stay fixed on 30, otherwise the algorithm doesn't work

        response = request_photos(params)
        logger.info(response.headers)
        response_json = parse_response(response)

        # Asychronously collect data
        upload_photo_metadata_to_gcs(
            response,
            response_json,
            gcp_credential_block_name,
            bucket_name,
            page_counter,
        )
        logger.info(
            f"Uploaded {len(response_json)} blobs to Google Cloud Storage Bucket: {bucket_name}"
        )

        number_new_stored_images += params["per_page"]
        logger.info(
            f"Number of new stored images in this data collection run: {number_new_stored_images}"
        )

        # Break the Loop if all pages have been processed
        page_counter += 1
        if page_counter > last_page_number:
            logger.info(
                "Downloaded metadata for all Editorial images of Unsplash platform"
            )
            break

        # Break the Loop if no more requests are possible
        requests_left = response.headers["X-Ratelimit-Remaining"]
        if requests_left == 0:
            logger.info(
                "No more requests left as Rate Limit is reached. Need to wait an hour"
            )
            break

        # Break the Loop if 300 images have been collected to avoid "OSError: [Errno 24] Too many open files"
        if number_new_stored_images == 300:
            logger.info(
                "Downloaded metadata for 300 Editorial images of Unsplash platform"
            )
            break


if __name__ == "__main__":
    ingest_photos_gcs(gcp_credential_block_name="unsplash-photo-trends-deployment-sa")
