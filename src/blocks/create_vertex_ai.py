"""Programmatically create Vertex AI Block for Prefect"""

from prefect_gcp import GcpCredentials, VertexAICustomTrainingJob

from src.utils import load_env_variables

env_vars = load_env_variables()
ENV = env_vars["ENV"]  # dev, test or prod

GCP_CREDENTIALS_PREFECT_BLOCK_NAME = (
    f"{env_vars['GCP_PROJECT_ID']}-{env_vars['GCP_DEPLOYMENT_SERVICE_ACCOUNT']}"
)
VERTEX_AI_BLOCK_NAME = f"{env_vars['GCP_PROJECT_ID']}-vertex-ai-{ENV}"

gcp_credentials = GcpCredentials.load(GCP_CREDENTIALS_PREFECT_BLOCK_NAME)
project_id = gcp_credentials.project
registry_adress = (
    f"{env_vars['GCP_DEFAULT_REGION']}-docker.pkg.dev/{project_id}/prefect-{ENV}"
)

vertext_ai_block = VertexAICustomTrainingJob(
    credentials=gcp_credentials,
    project_id=project_id,
    image=f"{registry_adress}/prefect:{env_vars['PREFECT_VERSION']}-python{env_vars['PYTHON_VERSION']}",
    region=env_vars["GCP_DEFAULT_REGION"],
).save(name=VERTEX_AI_BLOCK_NAME, overwrite=True)
