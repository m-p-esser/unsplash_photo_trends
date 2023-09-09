""" Collection of Extraction functions """

########## GCP ##############

from google.cloud import storage
from prefect_gcp import GcpCredentials


def download_blob_to_file(
    bucket_name: str,
    source_blob_name: str,
    destination_file_name: str,
    gcp_credential_block_name: str,
) -> storage.bucket.Bucket.blob:
    """Downloads a blob from the bucket."""
    # The ID of your GCS bucket
    # bucket_name = "your-bucket-name"

    # The ID of your GCS object
    # source_blob_name = "storage-object-name"

    # The path to which the file should be downloaded
    # destination_file_name = "local/path/to/file"

    gcp_credentials = GcpCredentials.load(gcp_credential_block_name)
    storage_client = gcp_credentials.get_cloud_storage_client()

    bucket = storage_client.bucket(bucket_name)

    # Construct a client side representation of a blob.
    # Note `Bucket.blob` differs from `Bucket.get_blob` as it doesn't retrieve
    # any content from Google Cloud Storage. As we don't need additional data,
    # using `Bucket.blob` is preferred here.
    blob = bucket.blob(source_blob_name)
    blob.download_to_filename(destination_file_name)

    # print(
    #     "Downloaded storage object {} from bucket {} to local file {}.".format(
    #         source_blob_name, bucket_name, destination_file_name
    #     )
    # )

    return blob


def download_blob_into_memory(
    bucket_name: str, blob_name: str, gcp_credential_block_name: str
) -> str:
    """Downloads a blob into memory."""
    # The ID of your GCS bucket
    # bucket_name = "your-bucket-name"

    # The ID of your GCS object
    # blob_name = "storage-object-name"

    gcp_credentials = GcpCredentials.load(gcp_credential_block_name)
    storage_client = gcp_credentials.get_cloud_storage_client()

    bucket = storage_client.bucket(bucket_name)

    # Construct a client side representation of a blob.
    # Note `Bucket.blob` differs from `Bucket.get_blob` as it doesn't retrieve
    # any content from Google Cloud Storage. As we don't need additional data,
    # using `Bucket.blob` is preferred here.
    blob = bucket.blob(blob_name)
    contents = blob.download_as_string()

    # print(
    #     "Downloaded storage object {} from bucket {} as the following string: {}.".format(
    #         blob_name, bucket_name, contents
    #     )
    # )
    return contents
