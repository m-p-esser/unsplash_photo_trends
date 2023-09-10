""" Collection of Extraction functions """

from google.cloud import storage
from prefect_gcp import GcpCredentials

########## GCP ##############


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
