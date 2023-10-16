"""Programmatically Store ENV variable as Prefect Variable """

from prefect import settings
from src.scripts.create_variables import (
    create_prefect_variable,
    update_prefect_variable_by_name,
)
from src.utils import load_env_variables

current_settings = settings.get_current_settings()
PREFECT_API_URL = current_settings.to_environment_variables()["PREFECT_API_URL"]
PREFECT_API_KEY = current_settings.to_environment_variables()["PREFECT_API_KEY"]


def create_env_string_variable():
    """Store ENV environment variable as Prefect Variable"""

    env_vars = load_env_variables()
    env = env_vars["ENV"]  # dev, test or prod
    gcp_project_id = env_vars["GCP_PROJECT_ID"].replace("-", "_")

    data = {"name": f"{gcp_project_id}_env", "value": env}
    print(data)

    response = create_prefect_variable(
        data=data, api_url=PREFECT_API_URL, api_key=PREFECT_API_KEY
    )
    print(f"Status Code: {response.status_code}")
    print(f"Status Reason: {response.reason}")
    print(response.content)

    # If Variable name exists, update instead (as a Variable name needs to be unique)
    if response.status_code == 409:
        response = update_prefect_variable_by_name(
            variable_name=data["name"],
            data=data,
            api_url=PREFECT_API_URL,
            api_key=PREFECT_API_KEY,
        )
        print(f"Status Code: {response.status_code}")
        print(f"Status Reason: {response.reason}")
        print(response.content)


if __name__ == "__main__":
    create_env_string_variable()
