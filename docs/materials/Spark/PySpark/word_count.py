import os
import sys

from pyspark.sql import SparkSession

PRODUCTION = True if ("PRODUCTION" in os.environ) else False

builder = SparkSession.builder.appName("Simple PySpark")

if not PRODUCTION:
    builder.master("local[*]")

spark = builder.getOrCreate()
spark.sparkContext.setLogLevel("ERROR")

data = []
with open(sys.argv[1]) as file:
    data = file.readlines()

rdd = spark.sparkContext.parallelize(data)

result = (
    rdd.flatMap(lambda item: item.split(" "))
    .map(lambda word: (word, 1))
    .reduceByKey(lambda a, b: a + b)
    .collect()
)

print(result)

spark.stop()
