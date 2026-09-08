# from tweepy import Client
# client = Client ( bearer_token = BEARER_TOKEN )
#
# result = client.search_recent_tweets (
#     query = "serbia"
# )
#
# for item in result.data:
#     print ( item )

BEARER_TOKEN = "..."

import os
import socket

from tweepy import StreamingClient

PRODUCTION = True if ("PRODUCTION" in os.environ) else False
SOCKET_IP = os.environ["SOCKET_IP"] if ("SOCKET_IP" in os.environ) else "localhost"
SOCKET_PORT = os.environ["SOCKET_PORT"] if ("SOCKET_PORT" in os.environ) else 9090
SPARKAPP_IP = os.environ["SPARKAPP_IP"] if ("SPARKAPP_IP" in os.environ) else "localhost"


class MyStreamingClient(StreamingClient):
    def __init__(self, bearer_token, connection):
        super().__init__(bearer_token=bearer_token)
        self.connection = connection

    def on_tweet(self, tweet):
        text = tweet.text
        # print ( text )
        self.connection.send(text.encode())


def twitter():
    msocket = socket.socket()
    msocket.bind((SOCKET_IP, SOCKET_PORT))
    msocket.listen()

    connection, address = msocket.accept()

    streaming_client = MyStreamingClient(BEARER_TOKEN, connection)
    streaming_client.sample()


from pyspark import SparkConf, SparkContext
from pyspark.streaming import StreamingContext


def process(time, rdd):
    print(time)
    for item in rdd.collect():
        print(item)


def spark():
    configuration = SparkConf()
    configuration.setAppName("Twitter PySpark")
    if not PRODUCTION:
        configuration.setMaster("local[*]")

    context = SparkContext(conf=configuration)
    context.setLogLevel("ERROR")

    streaming_context = StreamingContext(context, 2)

    dstream = streaming_context.socketTextStream(SPARKAPP_IP, SOCKET_IP)

    dstream.flatMap(lambda tweet: tweet.split(" ")).filter(lambda word: "#" in word).map(
        lambda word: (word, 1)
    ).reduceByKey(lambda a, b: a + b).foreachRDD(process)

    streaming_context.start()
    streaming_context.awaitTermination()


import threading

threading.Thread(target=twitter).start()
spark()
