""" Programmatically store selected, insensitive Environment Variables 
as Prefect Variables"""

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


def delete_prefect_variable_by_name(variable_name: str, api_url: str, api_key: str):
    """Delete Prefect Variable using Prefect REST Endpoint"""
    headers = {"Authorization": f"Bearer {api_key}"}
    endpoint = f"{api_url}/variables/name/{variable_name}"

    response = requests.delete(url=endpoint, headers=headers)
    return response


def update_prefect_variable_by_name(
    variable_name: str, data: dict, api_url: str, api_key: str
):
    """Update Prefect Variable using Prefect REST Endpoint"""
    headers = {"Authorization": f"Bearer {api_key}"}
    endpoint = f"{api_url}/variables/name/{variable_name}"

    response = requests.patch(url=endpoint, json=data, headers=headers)
    return response


if __name__ == "__main__":
    for k, v in insensitive_env_vars.items():
        data = {"name": k.lower(), "value": str(v)}
        response = create_prefect_variable(data, PREFECT_API_URL, PREFECT_API_KEY)

        # If Variable name exists, update instead (as a Variable name needs to be unique)
        if response.status_code == 409:
            response = update_prefect_variable_by_name(
                data["name"], PREFECT_API_URL, PREFECT_API_KEY
            )

        print(f"Status Code: {response.status_code}")
        print(f"Status Reason: {response.reason}")
        print(response.content)
