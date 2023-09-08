ARG PYTHON_VERSION
ARG PREFECT_VERSION

################################
# Install Linux OS
################################

FROM debian:bookworm-slim

################################
# Install Prefect and Python packages
################################

FROM prefecthq/prefect:${PREFECT_VERSION}-python${PYTHON_VERSION}

COPY requirements.txt requirements.txt
COPY setup.py setup.py
COPY make/.env make/.env

RUN pip install --no-cache-dir -r requirements.txt