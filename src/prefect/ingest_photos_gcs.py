""" Ingest actual photos (not metadata) to GCS using Download Links from Bigquery """

import datetime
from typing import Literal

from prefect_gcp.bigquery import bigquery_insert_stream, bigquery_query
from prefect_gcp.credentials import GcpCredentials

import prefect
from prefect import flow, get_run_logger
from prefect.task_runners import ConcurrentTaskRunner
from src.prefect.generic_tasks import (
    create_random_ua_string,
    prepare_proxy_adresses,
    request_unsplash_api,
    upload_file_to_gcs_bucket,
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

    logger.info(
        f"{len(results)} photos have been downloaded and stored in previous run"
    )

    return results


@flow(
    timeout_seconds=120,
    task_runner=ConcurrentTaskRunner(),
)  # Subflow (2nd level)
def request_photos(
    batch: list[tuple[str, str, datetime.datetime]],
    proxies: dict = None,
    headers: dict = None,
    params: dict = None,
    base_url: str = "https://images.unsplash.com",
) -> list[tuple[str, datetime.datetime, prefect.futures.PrefectFuture]]:
    """Asynchronously request images from Unsplash"""

    logger = get_run_logger()

    logger.info("Starting to request images from Unsplash")

    photos = []

    for photo in batch:
        endpoint = photo[1].replace(base_url, "")  # download path
        photo_id = photo[0]
        created_at = photo[2]

        future = request_unsplash_api.submit(
            endpoint, proxies, headers, params, base_url
        )
        photos.append((photo_id, created_at, future))

    # logger.info(f"Finished requesting images from Unsplash")

    return photos


@flow(
    timeout_seconds=120,
)  # Subflow (2nd level)
def upload_files_to_gcs_bucket(
    photos: list[tuple],
    gcp_credential_block_name: str,
    bucket_name: str,
    file_extension: str,
) -> list[tuple[str, prefect.futures.PrefectFuture]]:
    """Upload photos to GCS"""
    logger = get_run_logger()

    logger.info("Starting to upload photos to GCS")

    blobs = []
    for photo in photos:
        try:
            blob_name = upload_file_to_gcs_bucket(
                gcp_credential_block_name,
                bucket_name,
                photo[2].content,
                photo[0],  # photo id
                file_extension,
                f"{photo[1].year}-{photo[1].month}",  # created at
            )
            blobs.append((photo[0], blob_name))
        except Exception as e:
            logger.error(f"Exception occured: {e}")

    # logger.info("Finished uploading photos to GCS")

    return blobs


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
    """Flow to download photos from unsplash and store them in Google Cloud Storage Bucket"""

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

    # Isolate remaining photos and create a smaller subset
    remaining_photos = [p for p in downloadable_photos if p[0] in remaining_photo_ids][
        0:total_record_size
    ]
    # Split request load in batches
    batches = [
        remaining_photos[i : i + batch_size]
        for i in range(0, len(remaining_photo_ids), batch_size)
    ]

    if len(remaining_photo_ids) == 0:
        logger.info(f"Job finished")
        logger.info(f"All ({total_record_size}) photos downloaded")

    total_requested_photos = 0
    total_uploaded_photos = 0
    total_logged_records = 0
    total_records_iterated = 0

    while len(remaining_photos) > 0 and total_records_iterated < total_record_size:
        # Request and store photos
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
            photos = request_photos(batch, proxies, headers)
            requested_photos = [(p[0], p[1], p[2].result()) for p in photos]
            logger.info(f"Requested Photos: \n{requested_photos}")

            # Async - Upload photos to Google Cloud Storage
            bucket_name = f"photos-editorial-{env}"
            blobs = upload_files_to_gcs_bucket(
                requested_photos, gcp_credential_block_name, bucket_name, "jpg"
            )

            # # Store all sucessfully uploaded photo ids
            # uploaded_photos = [blob[0] for blob in blobs if blob[1].is_completed()]
            # uploaded_photos_ids = [
            #     p.split("/")[-1].split(".")[0] for p in uploaded_photos
            # ]
            # logger.info(f"Photo IDs of uploaded photos: {uploaded_photos_ids}")

            # Log written records to Bigquery
            download_log_records = []

            for p in requested_photos:
                photo_id = p[0]
                response = p[2]
                if response.status_code == 200 and photo_id in blobs:
                    request_url = str(response.request.url)
                    request_id = response.headers["x-imgix-id"]

                    download_log_record = {
                        "request_id": request_id,
                        "request_url": request_url,
                        "photo_id": photo_id,
                        "requested_at": datetime.datetime.now().strftime(
                            "%Y-%m-%d %H:%M:%S"
                        ),
                    }

                    download_log_records.append(download_log_record)

            logged_records = write_download_log_to_bigquery(
                gcp_credentials, download_log_records, env
            )

            total_requested_photos += len(requested_photos)
            # total_uploaded_photos += len(uploaded_photos)
            total_logged_records += len(download_log_records)
            total_records_iterated += batch_size

            logger.info("Batch processed")
            logger.info(f"Requested photos (in batch): {len(requested_photos)}")
            # logger.info(f"Uploaded photos (in batch): {len(uploaded_photos)}")
            logger.info(f"Records logged (in batch): {len(download_log_records)}")
            logger.info(f"Records iterated (in batch): {batch_size}")
            logger.info(f"Requested photos (in run): {total_requested_photos}")
            logger.info(f"Uploaded photos (in run): {total_uploaded_photos}")
            logger.info(f"Records logged (in run): {total_logged_records}")
            logger.info(f"Records iterated (in run): {total_records_iterated}")

            if total_records_iterated == total_record_size:
                logger.info(f"Iterated trough all records ({total_record_size})")
                logger.info("Job finished")
                break


if __name__ == "__main__":
    # @see https://github.com/PrefectHQ/prefect/pull/8983
    ingest_photos_gcs(
        gcp_credential_block_name="unsplash-photo-trends-deployment-sa",
        proxy_type="datacenter",
        batch_size=20,
        total_record_size=20,
    )
