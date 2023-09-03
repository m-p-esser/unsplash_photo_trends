""" Collection of Load functions """

########## GCP ##############

from google.cloud import storage
from prefect_gcp import GcpCredentials


def upload_blob_from_memory(
    bucket_name: str,
    contents,
    destination_blob_name: str,
    gcp_credential_block_name: str,
) -> storage.bucket.Bucket.blob:
    """Uploads a file to the bucket."""

    # The ID of your GCS bucket
    # bucket_name = "your-bucket-name"

    # The contents to upload to the file
    # contents = "these are my contents"

    # The ID of your GCS object
    # destination_blob_name = "storage-object-name"

    gcp_credentials = GcpCredentials.load(gcp_credential_block_name)
    storage_client = gcp_credentials.get_cloud_storage_client()

    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_string(contents)

    return blob


def upload_blob_from_file(
    bucket_name: str,
    source_file_name: str,
    destination_blob_name: str,
    gcp_credential_block_name: str,
) -> storage.bucket.Bucket.blob:
    """Uploads a file to the bucket."""
    # The ID of your GCS bucket
    # bucket_name = "your-bucket-name"
    # The path to your file to upload
    # source_file_name = "local/path/to/file"
    # The ID of your GCS object
    # destination_blob_name = "storage-object-name"

    gcp_credentials = GcpCredentials.load(gcp_credential_block_name)
    storage_client = gcp_credentials.get_cloud_storage_client()

    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_filename(source_file_name)

    return blob
