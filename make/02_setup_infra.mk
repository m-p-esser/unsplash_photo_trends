##@ [Infrastructure: Setup]

.PHONY: create-gcs-buckets
create-gcs-buckets: ### Create Google Cloud Storage Buckets
	gsutil mb -c standard -l ${GCP_DEFAULT_REGION} gs://unsplash-topics-dev || true
	gsutil mb -c standard -l ${GCP_DEFAULT_REGION} gs://unsplash-topics-test || true
	gsutil mb -c standard -l ${GCP_DEFAULT_REGION} gs://unsplash-topics-prod || true
	gsutil mb -c standard -l ${GCP_DEFAULT_REGION} gs://unsplash-monthly-platform-stats-dev || true
	gsutil mb -c standard -l ${GCP_DEFAULT_REGION} gs://unsplash-monthly-platform-stats-test || true
	gsutil mb -c standard -l ${GCP_DEFAULT_REGION} gs://unsplash-monthly-platform-stats-prod || true
	gsutil mb -c standard -l ${GCP_DEFAULT_REGION} gs://photos-editorial-metadata-dev || true
	gsutil mb -c standard -l ${GCP_DEFAULT_REGION} gs://photos-editorial-metadata-test || true
	gsutil mb -c standard -l ${GCP_DEFAULT_REGION} gs://photos-editorial-metadata-prod || true
	gsutil mb -c standard -l ${GCP_DEFAULT_REGION} gs://bucket-with-one-file|| true	
	gsutil mb -c standard -l ${GCP_DEFAULT_REGION} gs://photos-editorial-dev || true
	gsutil mb -c standard -l ${GCP_DEFAULT_REGION} gs://photos-editorial-test || true
	gsutil mb -c standard -l ${GCP_DEFAULT_REGION} gs://photos-editorial-prod || true
	gsutil mb -c standard -l ${GCP_DEFAULT_REGION} gs://task-runs-dev || true
	gsutil mb -c standard -l ${GCP_DEFAULT_REGION} gs://task-runs-test || true
	gsutil mb -c standard -l ${GCP_DEFAULT_REGION} gs://task-runs-prod || true
	gsutil mb -c standard -l ${GCP_DEFAULT_REGION} gs://task-runs-dev || true
	gsutil mb -c standard -l ${GCP_DEFAULT_REGION} gs://task-runs-test || true
	gsutil mb -c standard -l ${GCP_DEFAULT_REGION} gs://task-runs-prod || true

.PHONY: cleanup-gcs-buckets
cleanup-gcs-buckets: ### Delete all Contents from Google Cloud Storage Buckets
	gsutil rm gs://unsplash-topics-dev/**
	gsutil rm gs://unsplash-topics-test/**
	gsutil rm gs://unsplash-topics-prod/**