""" Collection of generic tasks that can be reused across flows """

import datetime
import json
import random
from tempfile import NamedTemporaryFile
from typing import Literal

import httpx
import pandas as pd
import requests
from fake_useragent import UserAgent
from google.cloud import storage

from prefect import get_run_logger, task
from prefect.blocks.system import Secret
from src.etl.load import upload_blob_from_file, upload_blob_from_memory


@task
def prepare_proxy_adresses(
    proxy_type=Literal["residential", "datacenter"],
) -> dict:
    """Prepare proxy adress to it can be used in a request"""

    allowed_proxy_types = ["residential", "datacenter"]
    if proxy_type not in allowed_proxy_types:
        raise ValueError(
            f"`proxy_type` '{proxy_type}' not allowed. Choose one of the following: {allowed_proxy_types}"
        )

    host = "brd.superproxy.io"
    port = 22225

    if proxy_type == "residential":
        prefect_block_prefix = "unsplash-photo-trends-bright-data"
        username = Secret.load(
            f"{prefect_block_prefix}-residential-proxy-username"
        ).get()
        password = Secret.load(
            f"{prefect_block_prefix}-residential-proxy-password"
        ).get()

    if proxy_type == "datacenter":
        prefect_block_prefix = "unsplash-photo-trends-bright-data"
        username = Secret.load(
            f"{prefect_block_prefix}-datacenter-proxy-username"
        ).get()
        password = Secret.load(
            f"{prefect_block_prefix}-datacenter-proxy-password"
        ).get()

    session_id = random.random()
    proxy_url = f"http://{username}-session-{session_id}:{password}@{host}:{port}"

    proxies = {"http": proxy_url, "https": proxy_url}

    return proxies


@task
def create_random_ua_string(
    browsers=["chrome", "firefox", "safari"], min_percentage=1.5
) -> str:
    """Creata a random Useragent string"""
    ua = UserAgent(browsers=browsers, min_percentage=min_percentage)
    random_useragent_string = ua.random

    return random_useragent_string


@task
def inspect_request(proxies: dict, headers: dict):
    """Request "http://httpbin.org/anything" to get information about machine requesting"""
    response = requests.get(
        "http://httpbin.org/anything",
        proxies=proxies,
        verify=False,
        headers=headers,
    )
    response.raise_for_status()

    return response.json()


@task(retries=3, retry_delay_seconds=10)
def request_unsplash_api(
    endpoint: str,
    proxies: dict = None,
    headers: dict = None,
    params: dict = {"per_page": 30},
    base_url: str = "https://api.unsplash.com",
) -> requests.Response:
    """Request data from Unsplash API Endpoint"""
    logger = get_run_logger()

    # Add API key to params if official API endpoint
    if base_url == "https://api.unsplash.com":
        params["client_id"] = Secret.load(
            "unsplash-photo-trends-unsplash-access-key"
        ).get()

    URI = base_url + endpoint

    logger.info(f"Requesting endpoint: {URI}")
    response = requests.get(
        url=URI, params=params, proxies=proxies, verify=False, headers=headers
    )

    response.raise_for_status()

    # Check Rate Limiting
    if base_url == "https://api.unsplash.com":
        rate_limit_limit = int(response.headers["X-Ratelimit-Limit"])
        rate_limit_remaining = int(response.headers["X-Ratelimit-Remaining"])
        consumed_quota = (rate_limit_limit - rate_limit_remaining) / rate_limit_limit

        if consumed_quota > 0.8:
            logger.warning(
                f"Rate limit almost reached: {consumed_quota*100} % of Quota consumed"
            )
            logger.warning(f"Remaining requests: {rate_limit_remaining}")

        if rate_limit_remaining == 0:
            logger.error(
                f"Rate limit reached: {consumed_quota*100} % of Quota consumed. Wait to continue"
            )

    return response


@task(
    # cache_key_fn=task_input_hash,
    # cache_expiration=datetime.timedelta(hours=1),
    timeout_seconds=20,
)
async def request_unsplash_api_async(
    endpoint: str,
    proxies: dict = None,
    headers: dict = None,
    params: dict = None,
    base_url="https://unsplash.com/napi",
):
    """Asynchrously request data Unsplash API endpoint"""
    logger = get_run_logger()

    async with httpx.AsyncClient(proxies=proxies, verify=False) as client:
        URI = base_url + endpoint

        logger.info(f"Requesting URI: {URI}")
        response = await client.get(url=URI, params=params, headers=headers)

        response.raise_for_status()

        return response


@task(
    # cache_key_fn=task_input_hash,
    # cache_expiration=datetime.timedelta(hours=1),
    timeout_seconds=20,
)
async def request_unsplash_images_async(
    endpoint: str,
    proxies: dict = None,
    headers: dict = None,
    params: dict = None,
    base_url="https://images.unsplash.com",
    **kwargs,
):
    logger = get_run_logger()

    async with httpx.AsyncClient(proxies=proxies, verify=False) as client:
        URI = base_url + endpoint

        logger.info(f"Requesting URI: {URI}")
        response = await client.get(url=URI, params=params, headers=headers)

        response.raise_for_status()

        if len(kwargs) > 0:
            kwargs["response"] = response
            return kwargs

        else:
            return response


@task(
    # cache_key_fn=task_input_hash,
    # cache_expiration=datetime.timedelta(hours=1),
    timeout_seconds=20,
)
def upload_file_to_gcs_bucket(
    gcp_credential_block_name: str,
    bucket_name: str,
    contents,
    file_name: str,
    file_extension: str,
    folder: str = None,
):
    logger = get_run_logger()

    if folder is None:
        blob_name = f"{file_name}.{file_extension}"
    else:
        blob_name = f"{folder}/{file_name}.{file_extension}"

    blob = upload_blob_from_memory(
        bucket_name, contents, blob_name, gcp_credential_block_name
    )

    logger.info(f"Uploaded {blob}: {blob_name} to {bucket_name}")

    return blob.name


@task(retries=3, retry_delay_seconds=10)
def parse_response(response: requests.Response) -> dict:
    """Convert Response to Dict"""
    logger = get_run_logger()

    response_json = response.json()

    logger.info(
        f"Response contains data for {len(response_json)} entries (rows or columns)"
    )

    return response_json


@task(retries=3, retry_delay_seconds=10)
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
