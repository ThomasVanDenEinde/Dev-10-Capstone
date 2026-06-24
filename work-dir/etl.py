from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("ExamplePySparkApp").getOrCreate()

print(spark)
print("\nETL goes here...\n")

spark.stop()