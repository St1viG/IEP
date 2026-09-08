import os

from pyspark.sql import SparkSession

PRODUCTION = True if ("PRODUCTION" in os.environ) else False

builder = SparkSession.builder.appName("Simple PySpark")

if not PRODUCTION:
    builder.master("local[*]")

spark = builder.getOrCreate()

data = ["I love python", "I love Spark", "I hate Spark"]

rdd = spark.sparkContext.parallelize(data)

result = rdd.filter(lambda item: "Spark" in item).collect()

print(result)

spark.stop()
