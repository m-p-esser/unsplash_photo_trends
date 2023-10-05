""" Collection of generic tasks that can be reused across flows """

import datetime
import json
import math
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
from prefect.tasks import task_input_hash
from src.etl.load import upload_blob_from_file
from src.utils import timer


@task
def prepare_proxy_adresses(method=Literal["bright-data", "zenrows"]) -> dict:
    """Prepare proxy adress to it can be used in a request"""
    acceptable_methods = ["bright-data", "zenrows"]
    if method not in acceptable_methods:
        raise ValueError(
            f"{method} is not an acceptable method. Allowed methods are: {acceptable_methods}"
        )

    if method == "zenrows":
        zenrows_api_key = Secret.load("unsplash-photo-trends-zenrows-api-key").get()
        proxy_url = f"http://{zenrows_api_key}:@proxy.zenrows.com:8001"

    if method == "bright-data":
        host = "brd.superproxy.io"
        port = 22225
        username = Secret.load(
            "unsplash-photo-trends-bright-data-residential-proxy-username"
        ).get()
        password = Secret.load(
            "unsplash-photo-trends-bright-data-residential-proxy-password"
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


@task
def check_zenrows_credits(zenrows_api_key: str) -> dict:
    """Check Zenrow Credits available"""
    response = requests.get(
        f"https://api.zenrows.com/v1/usage?apikey={zenrows_api_key}"
    )

    response.raise_for_status()

    credit_limit = int(response.json()["api_credit_limit"])
    credits_remaining = int(response.json()["api_credit_usage"])
    consumed_quota = (credits_remaining - credit_limit) / credit_limit

    return {
        "credit_limit": credit_limit,
        "credits_remaining": credits_remaining,
        "consumed_quote": consumed_quota,
    }


@task(retries=3, retry_delay_seconds=10)
@timer
def request_unsplash(
    endpoint: str, params: dict = {"per_page": 30}
) -> requests.Response:
    """Request data from Unsplash API"""
    logger = get_run_logger()

    params["client_id"] = Secret.load("unsplash-photo-trends-unsplash-access-key").get()
    BASE_URL = "https://api.unsplash.com"
    URI = BASE_URL + endpoint

    logger.info(f"Requesting endpoint: {URI}")
    response = requests.get(url=URI, params=params)

    response.raise_for_status()

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


@task(retries=3, retry_delay_seconds=10)
@timer
def request_unsplash_napi(
    endpoint: str,
    proxies: dict = None,
    headers: dict = None,
    params: dict = {"per_page": 30},
) -> requests.Response:
    """Request data from Unsplash API (napi, Backend API)"""
    logger = get_run_logger()

    BASE_URL = "https://unsplash.com/napi"
    URI = BASE_URL + endpoint

    logger.info(f"Requesting URI: {URI}")
    response = requests.get(
        url=URI, params=params, proxies=proxies, verify=False, headers=headers
    )

    response.raise_for_status()

    return response


@task(
    retries=3,
    retry_delay_seconds=3,
    cache_key_fn=task_input_hash,
    cache_expiration=datetime.timedelta(hours=1),
)
async def request_unsplash_napi_async(
    endpoint: str, proxies: dict = None, headers: dict = None, params: dict = None
):
    logger = get_run_logger()

    async with httpx.AsyncClient(proxies=proxies, verify=False) as client:
        BASE_URL = "https://unsplash.com/napi"
        URI = BASE_URL + endpoint

        # sleep_seconds = random.randint(1, 3)
        # logger.info(f"Sleeping for {sleep_seconds} seconds...")
        # await asyncio.sleep(sleep_seconds)

        logger.info(f"Requesting URI: {URI}")
        response = await client.get(url=URI, params=params, headers=headers)

        # logger.info(f"Request headers: \n {pformat(dict(response.request.headers))}")
        # logger.info(f"Response headers: \n {pformat(dict(response.headers))}")
        response.raise_for_status()

        return response


@task(retries=3, retry_delay_seconds=10)
@timer
def parse_response(response: requests.Response) -> dict:
    """Convert Response to Dict"""
    logger = get_run_logger()

    response_json = response.json()

    logger.info(
        f"Response contains data for {len(response_json)} entries (rows or columns)"
    )

    return response_json


@task(retries=3, retry_delay_seconds=10)
@timer
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
@timer
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


@task(retries=3, retry_delay_seconds=10)
@timer
def count_number_stored_files_in_gcs_bucket(storage_client, bucket_name: str) -> int:
    """Count the number of files / blobs stored in Google Cloud Storage Bucket"""

    logger = get_run_logger()

    bucket = storage_client.get_bucket(bucket_name)
    blobs = bucket.list_blobs()
    number_stored_files = sum(1 for _ in blobs)

    logger.info(f"Number of files in '{bucket.name}': {number_stored_files}")

    return int(number_stored_files)


@task(retries=3, retry_delay_seconds=10)
@timer
def get_processing_progress_from_response_header(
    response, number_stored_photos: int
) -> dict:
    """Use Response header data to calculate how many pages/objects have been processed
    and how many pages/objects still need to be processed"""

    logger = get_run_logger()

    number_requestable_objects = int(response.headers["X-Total"])
    number_objects_per_page = int(response.headers["X-Per-Page"])
    last_page_number = math.ceil(number_requestable_objects / number_objects_per_page)
    remaining_number_objects_to_request = (
        number_requestable_objects - number_stored_photos
    )
    number_processed_pages = math.floor(number_stored_photos / number_objects_per_page)

    processing_progress = {
        "number_requestable_objects": number_requestable_objects,
        "number_objects_per_page": number_objects_per_page,
        "last_page_number": last_page_number,
        "remaining_number_objects_to_request": remaining_number_objects_to_request,
        "number_processed_pages": number_processed_pages,
    }

    logger.info(processing_progress)

    return processing_progress
