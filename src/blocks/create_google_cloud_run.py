"""Programmatically create Google Cloud Run Block for Prefect"""

from prefect_gcp import CloudRunJob, GcpCredentials

from src.utils import load_env_variables

env_vars = load_env_variables()
ENV = env_vars["ENV"]  # dev, test or prod

GCP_CREDENTIALS_PREFECT_BLOCK_NAME = (
    f"{env_vars['GCP_PROJECT_ID']}-{env_vars['GCP_DEPLOYMENT_SERVICE_ACCOUNT']}"
)
GOOGLE_CLOUD_RUN_BLOCK_NAME = f"{env_vars['GCP_PROJECT_ID']}-google-cloud-run-{ENV}"

gcp_credentials = GcpCredentials.load(GCP_CREDENTIALS_PREFECT_BLOCK_NAME)
project_id = gcp_credentials.project
registry_adress = (
    f"{env_vars['GCP_DEFAULT_REGION']}-docker.pkg.dev/{project_id}/prefect-{ENV}"
)

cloud_run_job_block = CloudRunJob(
    credentials=gcp_credentials,
    project_id=project_id,
    image=f"{registry_adress}/prefect:{env_vars['PREFECT_VERSION']}-python{env_vars['PYTHON_VERSION']}",
    region=env_vars["GCP_DEFAULT_REGION"],
).save(name=GOOGLE_CLOUD_RUN_BLOCK_NAME, overwrite=True)
