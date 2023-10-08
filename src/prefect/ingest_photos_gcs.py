""" Ingest actual photos (not metadata) to GCS using Download Links from Bigquery """

import asyncio
import datetime
import faulthandler
from typing import Literal

from prefect_gcp.bigquery import bigquery_insert_stream, bigquery_query
from prefect_gcp.credentials import GcpCredentials

from prefect import flow, get_run_logger
from prefect.task_runners import ConcurrentTaskRunner
from src.prefect.generic_tasks import (
    create_random_ua_string,
    prepare_proxy_adresses,
    request_unsplash_napi_async,
    upload_file_to_gcs,
)
from src.utils import load_env_variables


@flow(
    retries=3,
    retry_delay_seconds=3,
)  # Subflow (2nd level)
def get_downloadable_photos_from_logs(
    gcp_credentials: GcpCredentials, env: str = "dev", location="europe-west3"
) -> list[tuple]:
    """Get all photos which have can be requested and downloaded"""

    logger = get_run_logger()

    query = f"""
            SELECT photo_id, urls.full, created_at
            FROM `unsplash-photo-trends.{env}.photos-editorial-metadata-expanded`
            ORDER BY created_at asc
            """

    results = bigquery_query(query, gcp_credentials, location=location)
    results = [(result[0], result[1], result[2]) for result in results]

    logger.info(f"There are {len(results)} photos available for download")

    return results


@flow(
    retries=3,
    retry_delay_seconds=3,
)  # Subflow (2nd level)
def get_downloaded_photos_from_logs(
    gcp_credentials: GcpCredentials, env: str = "dev", location="europe-west3"
) -> int:
    """Get all photos which have been requested and stored in GCS alrady"""

    logger = get_run_logger()

    query = f"""
            SELECT photo_id
            FROM `unsplash-photo-trends.{env}.photos-editorial-download-log`
            """

    results = bigquery_query(query, gcp_credentials, location=location)
    results = [result[0] for result in results]

    logger.info(f"Already downloaded {len(results)} photos")

    return results


@flow(timeout_seconds=60, task_runner=ConcurrentTaskRunner())  # Subflow (2nd level)
async def request_unsplash_napi(
    batch: list[tuple[str, str, datetime.datetime]],
    proxies: dict = None,
    headers: dict = None,
    params: dict = None,
    base_url: str = "https://images.unsplash.com",
):
    """Asynchronously request images from Unsplash"""

    logger = get_run_logger()

    logger.info("Starting to request images from Unsplash")

    tasks = [
        request_unsplash_napi_async(
            endpoint=photo[1].replace(base_url, ""),  # download path
            proxies=proxies,
            headers=headers,
            params=params,
            base_url=base_url,
            photo_id=photo[0],
            created_at=photo[
                2
            ],  # created at -> when has the photo been uploaded to unsplash
        )
        for photo in batch
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    logger.info("Finished requesting images from Unsplash")

    return results


@flow(timeout_seconds=60, task_runner=ConcurrentTaskRunner())  # Subflow (2nd level)
async def upload_files_to_gcs(
    results: list[dict],
    gcp_credential_block_name: str,
    bucket_name: str,
    file_extension: str,
):
    """Asynchonously upload photos to GCS"""
    logger = get_run_logger()

    logger.info("Starting to upload photos to GCS")

    futures = []
    for result in results:
        future = upload_file_to_gcs.submit(
            gcp_credential_block_name,
            bucket_name,
            result["response"].content,
            result["photo_id"],
            file_extension,
            f"{result['created_at'].year}-{result['created_at'].month}",
        )
        futures.append(future)

    logger.info("Finished uploading photos to GCS")

    return futures


@flow(retries=3, retry_delay_seconds=3)  # Subflow (2nd level)
def write_download_log_to_bigquery(
    gcp_credentials: GcpCredentials,
    records: list[dict],
    env: str = "dev",
    location="europe-west3",
):
    """Write for which URLs metadata has been requested and stored in Bigquery"""

    logger = get_run_logger()

    results = bigquery_insert_stream(
        env,
        "photos-editorial-download-log",
        records,
        gcp_credentials,
        location=location,
    )

    logger.info(
        f"Wrote {len(records)} rows to table 'unsplash-photo-trends.{env}.photos-editorial-download-log'"
    )

    return results


@flow
def ingest_photos_gcs(
    gcp_credential_block_name: str,
    proxy_type: Literal["datacenter", "residential"],
    batch_size: int,
    total_record_size: int,
):
    """Flow to download photos from unsplash and store them in GCS"""

    logger = get_run_logger()

    # Init all variables
    env_variables = load_env_variables()
    env = env_variables["ENV"]  # dev, test or prod

    # Init all credentials
    gcp_credentials = GcpCredentials.load(gcp_credential_block_name)

    # Get all downloadable photos (Bigquery)
    downloadable_photos = get_downloadable_photos_from_logs(gcp_credentials, env)

    # Get already downloaded photos (Bigquery)
    downloaded_photos = get_downloaded_photos_from_logs(gcp_credentials, env)

    # Compare both
    downloadable_photo_ids = [p[0] for p in downloadable_photos]
    remaining_photo_ids = set(downloadable_photo_ids).difference(set(downloaded_photos))

    if len(remaining_photo_ids) == 0:
        logger.info(f"Job finished")
        logger.info(f"All ({total_record_size}) photos downloaded")

    # Split request load in batches
    remaining_photos = [p for p in downloadable_photos if p[0] in remaining_photo_ids][
        0:total_record_size
    ]
    batches = [
        remaining_photos[i : i + batch_size]
        for i in range(0, len(remaining_photo_ids), batch_size)
    ]

    total_records_iterated = 0
    total_blobs_uploaded = 0

    while len(remaining_photos) > 0 and total_records_iterated < total_record_size:
        # Request and write data

        for batch in batches:
            # Prepare Proxy and Useragent
            proxies = prepare_proxy_adresses(proxy_type)
            proxies["http://"] = proxies["http"]
            proxies["https://"] = proxies["https"]
            proxies.pop("http")
            proxies.pop("https")

            useragent_string = create_random_ua_string()
            logger.info(f"Will be using '{useragent_string}' to make next requests")
            headers = {"User-Agent": useragent_string}  # Overwrite Useragent

            # Async - Request photos
            results = request_unsplash_napi(batch, proxies, headers)

            # Async - Upload photos to Blob Storage (using Photo ID as name)
            bucket_name = f"photos-editorial-{env}"
            futures = upload_files_to_gcs(
                results, gcp_credential_block_name, bucket_name, "jpg"
            )

            # Store all sucessfully uploaded photos
            uploaded_blobs = [
                future.result() for future in futures if not future.is_failed()
            ]
            uploaded_photo_ids = [
                blob.split("/")[-1].split(".")[0] for blob in uploaded_blobs
            ]

            total_blobs_uploaded += len(uploaded_blobs)

            # Log written records to Bigquery
            download_log_records = []

            for result in results:
                if (
                    result["response"].status_code == 200
                    and result["photo_id"] in uploaded_photo_ids
                ):
                    response = result["response"]
                    request_url = str(response.request.url)
                    request_id = response.headers["x-imgix-id"]
                    photo_id = result["photo_id"]

                    download_log_record = {
                        "request_id": request_id,
                        "request_url": request_url,
                        "photo_id": photo_id,
                        "requested_at": datetime.datetime.now().strftime(
                            "%Y-%m-%d %H:%M:%S"
                        ),
                    }

                    download_log_records.append(download_log_record)

            write_download_log_to_bigquery(gcp_credentials, download_log_records, env)

            total_records_iterated += batch_size
            logger.info(
                f"Batch processed: {len(download_log_records)} of {batch_size} blobs uploaded to GCS"
            )

            logger.info(
                f"In this run: {total_blobs_uploaded} of {total_records_iterated} blobs uploaded to GCS"
            )

            if total_records_iterated == total_record_size:
                logger.info(f"Job finished")
                logger.info(f"Iterated trough all records ({total_record_size})")
                break


if __name__ == "__main__":
    # @see https://github.com/PrefectHQ/prefect/pull/8983
    faulthandler.dump_traceback_later(60)
    ingest_photos_gcs(
        gcp_credential_block_name="unsplash-photo-trends-deployment-sa",
        proxy_type="datacenter",
        batch_size=20,
        total_record_size=20,
    )
