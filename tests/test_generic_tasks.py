import json

import pandas as pd
import requests
from google.cloud import storage

from prefect.logging import disable_run_logger
from src.prefect.generic_tasks import (
    create_random_ua_string,
    parse_response,
    prepare_proxy_adresses,
    request_unsplash_api,
    response_data_to_df,
    store_response_df_to_gcs_bucket,
)


def test_create_random_ua_string_successful():
    with disable_run_logger():
        random_ua_string = create_random_ua_string.fn()
        assert "Mozilla/5.0" in random_ua_string
        assert len(random_ua_string) > 0


def test_prepare_bright_data_proxies_successful():
    with disable_run_logger():
        proxies = prepare_proxy_adresses.fn(proxy_type="residential")
        assert len(proxies["http"]) > 0
        assert len(proxies["https"]) > 0


def test_request_unsplash_successful():
    with disable_run_logger():
        response = request_unsplash_api.fn(endpoint="/topics/")
        assert response.status_code == 200


def test_request_unsplash_napi_successful():
    with disable_run_logger():
        proxies = prepare_proxy_adresses.fn(proxy_type="residential")
        response = request_unsplash_api.fn(
            endpoint="/photos",
            proxies=proxies,
            params={"per_page": 30, "order_by": "oldest", "page": 1},
        )
        assert response.status_code == 200


# async def test_request_unsplash_napi_async_successful():
#     with disable_run_logger():
#         proxies = prepare_proxy_adresses.fn(proxy_type="residential")
#         response = await request_unsplash_napi_async.fn(
#             endpoint="/photos/3jUTmrmdNVg",
#             proxies=proxies,
#         )
#  assert response.status_code == 200


def test_parse_response_successful():
    with disable_run_logger():
        # Create an instance of the Response object
        response = requests.Response()

        # Manually set some attributes
        response.status_code = 200
        response._content = json.dumps({"message": "Hello, World!"}).encode("utf-8")
        response.url = "http://example.com"
        response.headers = {"Content-Type": "application/json"}

        response_json = parse_response.fn(response)
        assert isinstance(response_json, dict)


def test_flat_response_data_to_df_conversion_succeeded():
    with disable_run_logger():
        response_json = {
            "downloads": 103124778,
            "views": 12296623903,
            "new_photos": 89908,
            "new_photographers": 2158,
            "new_pixels": 1722181932213,
            "new_developers": 11025,
            "new_applications": 276,
            "new_requests": 1415432951,
        }
        df = response_data_to_df.fn(
            response_json=response_json, response_data_name="test"
        )
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0


def test_nested_response_data_to_df_conversion_succeeded():
    with disable_run_logger():
        response_json = [
            {
                "cover_photo": {
                    "alt_description": "topless boy looking at round silver ornament",
                    "blur_hash": "LNB|Niof00of9Fxu-;RjIAayxuM{",
                    "breadcrumbs": [],
                    "color": "#262626",
                    "created_at": "2020-04-20T08:45:16Z",
                    "current_user_collections": [],
                    "description": None,
                    "height": 5704,
                    "id": "hwUxEG1dTig",
                    "liked_by_user": False,
                    "likes": 167,
                    "links": {
                        "download": "https://unsplash.com/photos/hwUxEG1dTig/download",
                        "download_location": "https://api.unsplash.com/photos/hwUxEG1dTig/download",
                        "html": "https://unsplash.com/photos/hwUxEG1dTig",
                        "self": "https://api.unsplash.com/photos/hwUxEG1dTig",
                    },
                    "promoted_at": "2020-04-20T16:45:01Z",
                    "slug": "hwUxEG1dTig",
                    "sponsorship": None,
                    "topic_submissions": {
                        "fashion-beauty": {
                            "approved_on": "2020-09-10T14:16:44Z",
                            "status": "approved",
                        },
                        "monochromatic": {
                            "approved_on": "2023-09-01T20:43:09Z",
                            "status": "approved",
                        },
                    },
                    "updated_at": "2023-09-02T21:12:15Z",
                    "urls": {
                        "full": "https://images.unsplash.com/photo-1587372170565-bc6930f7e221?ixlib=rb-4.0.3&q=85&fm=jpg&crop=entropy&cs=srgb",
                        "raw": "https://images.unsplash.com/photo-1587372170565-bc6930f7e221?ixlib=rb-4.0.3",
                        "regular": "https://images.unsplash.com/photo-1587372170565-bc6930f7e221?ixlib=rb-4.0.3&q=80&fm=jpg&crop=entropy&cs=tinysrgb&w=1080&fit=max",
                        "small": "https://images.unsplash.com/photo-1587372170565-bc6930f7e221?ixlib=rb-4.0.3&q=80&fm=jpg&crop=entropy&cs=tinysrgb&w=400&fit=max",
                        "small_s3": "https://s3.us-west-2.amazonaws.com/images.unsplash.com/small/photo-1587372170565-bc6930f7e221",
                        "thumb": "https://images.unsplash.com/photo-1587372170565-bc6930f7e221?ixlib=rb-4.0.3&q=80&fm=jpg&crop=entropy&cs=tinysrgb&w=200&fit=max",
                    },
                    "user": {
                        "accepted_tos": True,
                        "bio": "ID instagram : shahinkhalaji.art\r\n",
                        "first_name": "shahin",
                        "for_hire": True,
                        "id": "1f5kN9wmwig",
                        "instagram_username": "shahin.khalajii",
                        "last_name": "khalaji",
                        "links": {
                            "followers": "https://api.unsplash.com/users/shahinkhalaji/followers",
                            "following": "https://api.unsplash.com/users/shahinkhalaji/following",
                            "html": "https://unsplash.com/@shahinkhalaji",
                            "likes": "https://api.unsplash.com/users/shahinkhalaji/likes",
                            "photos": "https://api.unsplash.com/users/shahinkhalaji/photos",
                            "portfolio": "https://api.unsplash.com/users/shahinkhalaji/portfolio",
                            "self": "https://api.unsplash.com/users/shahinkhalaji",
                        },
                        "location": "tehran",
                        "name": "shahin khalaji",
                        "portfolio_url": None,
                        "profile_image": {
                            "large": "https://images.unsplash.com/profile-1642764399615-7485ff941deaimage?ixlib=rb-4.0.3&crop=faces&fit=crop&w=128&h=128",
                            "medium": "https://images.unsplash.com/profile-1642764399615-7485ff941deaimage?ixlib=rb-4.0.3&crop=faces&fit=crop&w=64&h=64",
                            "small": "https://images.unsplash.com/profile-1642764399615-7485ff941deaimage?ixlib=rb-4.0.3&crop=faces&fit=crop&w=32&h=32",
                        },
                        "social": {
                            "instagram_username": "shahin.khalajii",
                            "paypal_email": None,
                            "portfolio_url": None,
                            "twitter_username": "Shahinkhalaji11",
                        },
                        "total_collections": 0,
                        "total_likes": 53,
                        "total_photos": 375,
                        "twitter_username": "Shahinkhalaji11",
                        "updated_at": "2023-09-03T11:30:19Z",
                        "username": "shahinkhalaji",
                    },
                    "width": 4000,
                },
                "current_user_contributions": [],
                "description": "Capture the essence of timelessness through the art of monochrome. Show us how you immerse yourself in a world of contrast, texture, and emotion where every shade tells a story. Evoke a symphony of feelings, showcasing the interplay between light and shadow in its purest form.",
                "ends_at": "2023-09-30T23:59:59Z",
                "featured": True,
                "id": "3bnm95isIxE",
                "links": {
                    "html": "https://unsplash.com/t/monochromatic",
                    "photos": "https://api.unsplash.com/topics/monochromatic/photos",
                    "self": "https://api.unsplash.com/topics/monochromatic",
                },
                "only_submissions_after": None,
                "owners": [
                    {
                        "accepted_tos": True,
                        "bio": "Behind the scenes of the team building the internet\u2019s open library of freely useable visuals.",
                        "first_name": "Unsplash",
                        "for_hire": False,
                        "id": "QV5S1rtoUJ0",
                        "instagram_username": "unsplash",
                        "last_name": None,
                        "links": {
                            "followers": "https://api.unsplash.com/users/unsplash/followers",
                            "following": "https://api.unsplash.com/users/unsplash/following",
                            "html": "https://unsplash.com/@unsplash",
                            "likes": "https://api.unsplash.com/users/unsplash/likes",
                            "photos": "https://api.unsplash.com/users/unsplash/photos",
                            "portfolio": "https://api.unsplash.com/users/unsplash/portfolio",
                            "self": "https://api.unsplash.com/users/unsplash",
                        },
                        "location": "Montreal, Canada",
                        "name": "Unsplash",
                        "portfolio_url": "https://unsplash.com",
                        "profile_image": {
                            "large": "https://images.unsplash.com/profile-1544707963613-16baf868f301?ixlib=rb-4.0.3&crop=faces&fit=crop&w=128&h=128",
                            "medium": "https://images.unsplash.com/profile-1544707963613-16baf868f301?ixlib=rb-4.0.3&crop=faces&fit=crop&w=64&h=64",
                            "small": "https://images.unsplash.com/profile-1544707963613-16baf868f301?ixlib=rb-4.0.3&crop=faces&fit=crop&w=32&h=32",
                        },
                        "social": {
                            "instagram_username": "unsplash",
                            "paypal_email": None,
                            "portfolio_url": "https://unsplash.com",
                            "twitter_username": "unsplash",
                        },
                        "total_collections": 8,
                        "total_likes": 16095,
                        "total_photos": 29,
                        "twitter_username": "unsplash",
                        "updated_at": "2023-09-01T16:43:58Z",
                        "username": "unsplash",
                    }
                ],
                "preview_photos": [
                    {
                        "blur_hash": "LNB|Niof00of9Fxu-;RjIAayxuM{",
                        "created_at": "2020-04-20T08:45:16Z",
                        "id": "hwUxEG1dTig",
                        "slug": "hwUxEG1dTig",
                        "updated_at": "2023-09-02T21:12:15Z",
                        "urls": {
                            "full": "https://images.unsplash.com/photo-1587372170565-bc6930f7e221?ixlib=rb-4.0.3&q=85&fm=jpg&crop=entropy&cs=srgb",
                            "raw": "https://images.unsplash.com/photo-1587372170565-bc6930f7e221?ixlib=rb-4.0.3",
                            "regular": "https://images.unsplash.com/photo-1587372170565-bc6930f7e221?ixlib=rb-4.0.3&q=80&fm=jpg&crop=entropy&cs=tinysrgb&w=1080&fit=max",
                            "small": "https://images.unsplash.com/photo-1587372170565-bc6930f7e221?ixlib=rb-4.0.3&q=80&fm=jpg&crop=entropy&cs=tinysrgb&w=400&fit=max",
                            "small_s3": "https://s3.us-west-2.amazonaws.com/images.unsplash.com/small/photo-1587372170565-bc6930f7e221",
                            "thumb": "https://images.unsplash.com/photo-1587372170565-bc6930f7e221?ixlib=rb-4.0.3&q=80&fm=jpg&crop=entropy&cs=tinysrgb&w=200&fit=max",
                        },
                    },
                    {
                        "blur_hash": "LhPq.:0LN^WW-osAWCa{w]xtRkWC",
                        "created_at": "2019-10-31T08:15:51Z",
                        "id": "_UrvVQh5cyo",
                        "slug": "_UrvVQh5cyo",
                        "updated_at": "2023-09-03T03:09:36Z",
                        "urls": {
                            "full": "https://images.unsplash.com/photo-1572509636870-afd5ae876afb?ixlib=rb-4.0.3&q=85&fm=jpg&crop=entropy&cs=srgb",
                            "raw": "https://images.unsplash.com/photo-1572509636870-afd5ae876afb?ixlib=rb-4.0.3",
                            "regular": "https://images.unsplash.com/photo-1572509636870-afd5ae876afb?ixlib=rb-4.0.3&q=80&fm=jpg&crop=entropy&cs=tinysrgb&w=1080&fit=max",
                            "small": "https://images.unsplash.com/photo-1572509636870-afd5ae876afb?ixlib=rb-4.0.3&q=80&fm=jpg&crop=entropy&cs=tinysrgb&w=400&fit=max",
                            "small_s3": "https://s3.us-west-2.amazonaws.com/images.unsplash.com/small/photo-1572509636870-afd5ae876afb",
                            "thumb": "https://images.unsplash.com/photo-1572509636870-afd5ae876afb?ixlib=rb-4.0.3&q=80&fm=jpg&crop=entropy&cs=tinysrgb&w=200&fit=max",
                        },
                    },
                    {
                        "blur_hash": "L668EXxuRj%M00M{t7M{?bxuRjof",
                        "created_at": "2021-02-06T14:19:26Z",
                        "id": "rmKkZqnVtk4",
                        "slug": "rmKkZqnVtk4",
                        "updated_at": "2023-09-03T00:18:17Z",
                        "urls": {
                            "full": "https://images.unsplash.com/photo-1612620980838-5541dad8e254?ixlib=rb-4.0.3&q=85&fm=jpg&crop=entropy&cs=srgb",
                            "raw": "https://images.unsplash.com/photo-1612620980838-5541dad8e254?ixlib=rb-4.0.3",
                            "regular": "https://images.unsplash.com/photo-1612620980838-5541dad8e254?ixlib=rb-4.0.3&q=80&fm=jpg&crop=entropy&cs=tinysrgb&w=1080&fit=max",
                            "small": "https://images.unsplash.com/photo-1612620980838-5541dad8e254?ixlib=rb-4.0.3&q=80&fm=jpg&crop=entropy&cs=tinysrgb&w=400&fit=max",
                            "small_s3": "https://s3.us-west-2.amazonaws.com/images.unsplash.com/small/photo-1612620980838-5541dad8e254",
                            "thumb": "https://images.unsplash.com/photo-1612620980838-5541dad8e254?ixlib=rb-4.0.3&q=80&fm=jpg&crop=entropy&cs=tinysrgb&w=200&fit=max",
                        },
                    },
                    {
                        "blur_hash": "LIKdPVRj_NRO~Wj?xut7E1ofIAR+",
                        "created_at": "2019-03-12T07:03:25Z",
                        "id": "d2s8NQ6WD24",
                        "slug": "d2s8NQ6WD24",
                        "updated_at": "2023-09-02T15:06:18Z",
                        "urls": {
                            "full": "https://images.unsplash.com/photo-1552374196-1ab2a1c593e8?ixlib=rb-4.0.3&q=85&fm=jpg&crop=entropy&cs=srgb",
                            "raw": "https://images.unsplash.com/photo-1552374196-1ab2a1c593e8?ixlib=rb-4.0.3",
                            "regular": "https://images.unsplash.com/photo-1552374196-1ab2a1c593e8?ixlib=rb-4.0.3&q=80&fm=jpg&crop=entropy&cs=tinysrgb&w=1080&fit=max",
                            "small": "https://images.unsplash.com/photo-1552374196-1ab2a1c593e8?ixlib=rb-4.0.3&q=80&fm=jpg&crop=entropy&cs=tinysrgb&w=400&fit=max",
                            "small_s3": "https://s3.us-west-2.amazonaws.com/images.unsplash.com/small/photo-1552374196-1ab2a1c593e8",
                            "thumb": "https://images.unsplash.com/photo-1552374196-1ab2a1c593e8?ixlib=rb-4.0.3&q=80&fm=jpg&crop=entropy&cs=tinysrgb&w=200&fit=max",
                        },
                    },
                ],
                "published_at": "2023-08-15T17:48:03Z",
                "slug": "monochromatic",
                "starts_at": "2023-09-01T00:00:00Z",
                "status": "open",
                "title": "Monochromatic",
                "total_current_user_submissions": None,
                "total_photos": 119,
                "updated_at": "2023-09-01T20:43:20Z",
                "visibility": "featured",
            }
        ]
        df = response_data_to_df.fn(
            response_json=response_json, response_data_name="test"
        )
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0


def test_store_response_df_to_gcs_bucket_succeeded():
    with disable_run_logger():
        response_data = {
            "Name": ["Alice", "Bob", "Charlie", "David"],
            "Age": [25, 30, 35, 40],
            "City": ["New York", "Los Angeles", "Chicago", "Houston"],
        }

        df = pd.DataFrame(response_data)
        blob = store_response_df_to_gcs_bucket.fn(
            df=df, response_data_name="unit-tests", env="dev"
        )
        assert isinstance(blob, storage.blob.Blob)
        assert blob.size > 0  # Size is greater than 0 if the blob contains data
