""" Programmatically store selected, insensitive Environment Variables 
as Prefect Variables"""

from pprint import pformat

import requests

from prefect import settings
from src.utils import load_env_variables

current_settings = settings.get_current_settings()
PREFECT_API_URL = current_settings.to_environment_variables()["PREFECT_API_URL"]
PREFECT_API_KEY = current_settings.to_environment_variables()["PREFECT_API_KEY"]

env_vars = dict(load_env_variables())
sensitive_strings = ["USER", "PASSWORD", "KEY", "ACCOUNT", "EMAIL", "USERNAME", "ENV"]

insensitive_env_vars = {
    key: value
    for key, value in env_vars.items()
    if all(s not in key for s in sensitive_strings)
}


def create_prefect_variable(data: dict, api_url: str, api_key: str):
    """Create Prefect Variable using Prefect REST Endpoint"""
    headers = {"Authorization": f"Bearer {api_key}"}
    endpoint = f"{api_url}/variables/"

    response = requests.post(url=endpoint, headers=headers, json=data)
    return response


if __name__ == "__main__":
    for k, v in insensitive_env_vars.items():
        data = {"name": k.lower(), "value": str(v)}
        response = create_prefect_variable(data, PREFECT_API_URL, PREFECT_API_KEY)
        print(pformat(response.json()))
