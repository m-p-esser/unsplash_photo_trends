##@ [Flow: Deployment]

.PHONY: deploy-pyspark-hello-world
deploy-pyspark-hello-world: ### Basic Pyspark Job
	gsutil cp src/spark/hello_pyspark.py gs://${SPARK_STAGING_BUCKET_NAME}/hello_pyspark.py

