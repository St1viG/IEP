import os

from pyspark.sql import SparkSession

PRODUCTION = True if ("PRODUCTION" in os.environ) else False
DATABASE_IP = os.environ["DATABASE_IP"] if ("DATABASE_IP" in os.environ) else "localhost"

builder = SparkSession.builder.appName("PySpark Database example")

if not PRODUCTION:
    builder = builder.master("local[*]").config(
        "spark.driver.extraClassPath", "mysql-connector-j-8.0.33.jar"
    )


spark = builder.getOrCreate()

people_data_frame = (
    spark.read.format("jdbc")
    .option("driver", "com.mysql.cj.jdbc.Driver")
    .option("url", f"jdbc:mysql://{DATABASE_IP}:3306/mockaroo")
    .option("dbtable", "mockaroo.people")
    .option("user", "root")
    .option("password", "root")
    .load()
)

messages_data_frame = (
    spark.read.format("jdbc")
    .option("driver", "com.mysql.cj.jdbc.Driver")
    .option("url", f"jdbc:mysql://{DATABASE_IP}:3306/mockaroo")
    .option("dbtable", "mockaroo.messages")
    .option("user", "root")
    .option("password", "root")
    .load()
)

# people_data_frame.show ( )
# result = people_data_frame.filter ( people_data_frame["gender"] == "Male" ).collect ( )
# print ( result )

result = (
    people_data_frame.join(
        messages_data_frame, messages_data_frame["person_id"] == people_data_frame["id"]
    )
    .groupBy(people_data_frame["first_name"])
    .count()
    .collect()
)
print(result)

spark.stop()
