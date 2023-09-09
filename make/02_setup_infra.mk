##@ [Infrastructure: Setup]

.PHONY: create-gcs-buckets
create-gcs-buckets: ### Create Google Cloud Storage Buckets
	gsutil mb -c standard -l ${GCP_DEFAULT_REGION} gs://unsplash-topics-dev
	gsutil mb -c standard -l ${GCP_DEFAULT_REGION} gs://unsplash-topics-test
	gsutil mb -c standard -l ${GCP_DEFAULT_REGION} gs://unsplash-topics-prod

.PHONY: cleanup-gcs-buckets
cleanup-gcs-buckets: ### Delete all Contents from Google Cloud Storage Buckets
	gsutil rm gs://unsplash-topics-dev/**
	gsutil rm gs://unsplash-topics-test/**
	gsutil rm gs://unsplash-topics-prod/**