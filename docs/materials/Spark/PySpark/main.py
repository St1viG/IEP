from flask import Flask, request

application = Flask(__name__)

import os
import subprocess


@application.route("/simple")
def simple():
    os.environ["SPARK_APPLICATION_PYTHON_LOCATION"] = "/app/simple.py"
    result = subprocess.check_output(["/template.sh"])
    return result.decode()


@application.route("/words", methods=["POST"])
def words():
    file = request.files["file"]
    file.save("/app/words.txt")

    os.environ["SPARK_APPLICATION_PYTHON_LOCATION"] = "/app/word_count.py"
    os.environ["SPARK_APPLICATION_ARGS"] = "/app/words.txt"

    result = subprocess.check_output(["/template.sh"])
    return result.decode()


@application.route("/database")
def database():
    os.environ["SPARK_APPLICATION_PYTHON_LOCATION"] = "/app/database.py"

    os.environ["SPARK_SUBMIT_ARGS"] = (
        "--driver-class-path /app/mysql-connector-j-8.0.33.jar --jars /app/mysql-connector-j-8.0.33.jar"
    )

    result = subprocess.check_output(["/template.sh"])
    return result.decode()


if __name__ == "__main__":
    application.run(host="0.0.0.0")
