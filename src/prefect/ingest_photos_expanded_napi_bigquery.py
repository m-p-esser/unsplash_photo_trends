""" Flow to request https://unsplash.com/napi/photos/<photo_id> Endpoint (Backend API) 
to receive editorial metadata and store it in Bigquery """

import asyncio
import datetime
from typing import Literal

from prefect_gcp.bigquery import bigquery_insert_stream, bigquery_query
from prefect_gcp.credentials import GcpCredentials

from prefect import flow, get_run_logger
from src.data_types import PhotoEditorialMetadataExpanded
from src.decoder import datetime_decoder
from src.prefect.generic_tasks import (
    create_random_ua_string,
    prepare_proxy_adresses,
    request_unsplash_api_async,
)
from src.utils import load_env_variables, timer


@flow(
    retries=3,
    retry_delay_seconds=10,
)  # Subflow (2nd level)
def get_requested_photos_from_logs(
    gcp_credentials: GcpCredentials, env: str = "dev", location="europe-west3"
) -> int:
    """Get all photos which have been requested and stored in Bigquery Log tablealready"""

    logger = get_run_logger()

    query = f"""
            SELECT photo_id
            FROM `unsplash-photo-trends.{env}.photos-editorial-metadata-expanded-request-log`
        """

    results = bigquery_query(query, gcp_credentials, location=location)
    results = [result[0] for result in results]

    logger.info(
        f"Already requested expanded metadata for {len(results)} photos in previous runs"
    )

    return results


@flow(timeout_seconds=120)  # Subflow (2nd level)
async def request_unsplash_api(
    batch: list[str], proxies: dict = None, headers: dict = None, params: dict = None
):
    endpoints = [f"/photos/{photo_id}" for photo_id in batch]
    tasks = [
        request_unsplash_api_async(endpoint, proxies, headers, params)
        for endpoint in endpoints
    ]
    responses = await asyncio.gather(*tasks, return_exceptions=True)

    return responses


@flow(retries=3, retry_delay_seconds=10)  # Subflow (2nd level)
def write_photo_metadata_expanded_to_bigquery(
    gcp_credentials: GcpCredentials,
    records: list[dict],
    env: str = "dev",
    location="europe-west3",
):
    """Write expanded photo metadata to Bigquery"""

    logger = get_run_logger()

    results = bigquery_insert_stream(
        env,
        "photos-editorial-metadata-expanded",
        records,
        gcp_credentials,
        location=location,
    )

    logger.info(
        f"Wrote {len(records)} rows to table 'unsplash-photo-trends.{env}.photos-editorial-metadata-expanded'"
    )

    return results


@flow(retries=3, retry_delay_seconds=10)  # Subflow (2nd level)
def write_request_log_to_bigquery(
    gcp_credentials: GcpCredentials,
    records: list[dict],
    env: str = "dev",
    location="europe-west3",
):
    """Write for which URLs metadata has been requested and stored in Bigquery"""

    logger = get_run_logger()

    results = bigquery_insert_stream(
        env,
        "photos-editorial-metadata-expanded-request-log",
        records,
        gcp_credentials,
        location=location,
    )

    logger.info(
        f"Wrote {len(records)} rows to table 'unsplash-photo-trends.{env}.photos-editorial-metadata-expanded-request-log'"
    )

    return results


@flow(timeout_seconds=180)  # Main Flow (1st level) # Main Flow (1st level)
@timer
def ingest_photos_expanded_napi_bigquery(
    gcp_credential_block_name: str,
    proxy_type: Literal["datacenter", "residential"],
    batch_size: int = 30,
    total_record_size: int = 300,
):
    """Flow to load editorial photo metadata from Unsplash and store them in Bigquery"""

    logger = get_run_logger()

    # Init all variables
    env_variables = load_env_variables()
    env = env_variables["ENV"]  # dev, test or prod
    source_bucket_name = f"photos-editorial-metadata-{env}"

    # Init all credentials
    gcp_credentials = GcpCredentials.load(gcp_credential_block_name)

    # Get all Photos
    storage_client = gcp_credentials.get_cloud_storage_client()
    logger.info(f"Collecting blobs from bucket '{source_bucket_name}'")
    blobs = storage_client.list_blobs(source_bucket_name, page_size=10000)
    pages = blobs.pages
    photo_ids = []
    for idx, page in enumerate(pages):
        blob_names = [str(blob.name).split(".")[0] for blob in page]
        photo_ids.extend(blob_names)
        logger.info(f"Collected blobs from page {idx+1}")
    logger.info(f"{len(photo_ids)} Photos stored in {source_bucket_name}")

    # Get all previously requested photos (where expanded photo metadata is available)
    requested_photo_ids = get_requested_photos_from_logs(gcp_credentials, env)
    logger.info(
        f"{len(requested_photo_ids)} Photos with expanded metadata written to 'photos-editorial-metadata-expanded-request-log'"
    )

    # Compare both lists and get photo id that need to be requested
    remaining_photo_ids = list(set(photo_ids).difference(set(requested_photo_ids)))
    logger.info(
        f"{len(remaining_photo_ids)} Photos still need to requested from https://unsplash.com/napi/photos/<photo_id> "
    )

    # Prepare Proxy and Useragent
    proxies = prepare_proxy_adresses(proxy_type)
    proxies["http://"] = proxies["http"]
    proxies["https://"] = proxies["https"]
    proxies.pop("http")
    proxies.pop("https")

    # Split request load in batches
    remaining_photo_ids = remaining_photo_ids[0:total_record_size]
    batches = [
        remaining_photo_ids[i : i + batch_size]
        for i in range(0, len(remaining_photo_ids), batch_size)
    ]

    if len(remaining_photo_ids) == 0:
        logger.info(f"Job finished")
        logger.info(
            f"All ({total_record_size}) metadata (and log) records written to Bigquery"
        )

    total_records_written = 0

    while len(remaining_photo_ids) > 0 and total_records_written < total_record_size:
        # Request and write data

        for batch in batches:
            useragent_string = create_random_ua_string()
            logger.info(f"Will be using '{useragent_string}' to make next requests")
            headers = {"User-Agent": useragent_string}  # Overwrite Useragent

            responses = request_unsplash_api(batch, proxies, headers)

            # Write photo metadata records to Bigquery
            records_photo_metadata = []

            for response in responses:
                try:
                    response_json = response.json(object_hook=datetime_decoder)
                    response_json["requested_at"] = datetime.datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )

                    # This class initialization makes sure to filter the response by only keeping relevant keys
                    photo_editorial_metadata_expanded = (
                        PhotoEditorialMetadataExpanded.from_dict(response_json)
                    )

                    # Convert back to dict so it can be written to Bigquery
                    record_photo_metadata = photo_editorial_metadata_expanded.to_dict()
                    record_photo_metadata["photo_id"] = record_photo_metadata["id"]
                    record_photo_metadata.pop("id", None)
                    records_photo_metadata.append(record_photo_metadata)
                except Exception as e:
                    logger.error(f"Exception occured: {e}")

            if len(records_photo_metadata) == 0:
                logger.info("Didn't collect any metadata. Moving on to new batch")
                continue

            write_photo_metadata_expanded_to_bigquery(
                gcp_credentials, records_photo_metadata, env
            )

            # Log written records to Bigquery
            request_log_records = []

            for response in responses:
                try:
                    response_json = response.json()
                    request_url = str(response.request.url)
                    request_id = response.headers["x-request-id"]
                    photo_id = response_json["id"]

                    request_log_record = {
                        "request_id": request_id,
                        "request_url": request_url,
                        "photo_id": photo_id,
                        "requested_at": datetime.datetime.now().strftime(
                            "%Y-%m-%d %H:%M:%S"
                        ),
                    }

                    request_log_records.append(request_log_record)
                except Exception as e:
                    logger.error(f"Exception occured: {e}")

            write_request_log_to_bigquery(gcp_credentials, request_log_records, env)

            total_records_written += batch_size
            logger.info(
                f"Batch processed: {batch_size} metadata (and log) records written to Bigquery"
            )
            logger.info(
                f"In this run: {total_records_written} metadata (and log) records written to Bigquery"
            )

            if total_records_written == 300:
                logger.info(f"Job finished")
                logger.info(
                    f"All ({total_record_size}) metadata (and log) records written to Bigquery"
                )
                break


if __name__ == "__main__":
    ingest_photos_expanded_napi_bigquery(
        gcp_credential_block_name="unsplash-photo-trends-deployment-sa",
        proxy_type="datacenter",
        batch_size=30,
        total_record_size=300,
    )
