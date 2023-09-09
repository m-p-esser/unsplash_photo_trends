##@ [Infrastructure: Setup]

.PHONY: create-gcs-buckets
create-gcs-buckets: ### Create Google Cloud Storage Buckets
	gsutil mb -c standard -l ${GCP_DEFAULT_REGION} gs://unsplash-topics-dev
	gsutil mb -c standard -l ${GCP_DEFAULT_REGION} gs://unsplash-topics-test
	gsutil mb -c standard -l ${GCP_DEFAULT_REGION} gs://unsplash-topics-prod
