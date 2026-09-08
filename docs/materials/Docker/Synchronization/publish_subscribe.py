from redis import Redis


def publish(data):
    with Redis(host="localhost", port=6379, db=0) as redis:
        redis.publish("channel", data)


import random
import time


def publisher(id):
    while True:
        data = "VALUE = " + str(random.randint(0, 10))
        publish(data)
        print(f"PUBLISHER{id} = {data}")
        time.sleep(1.5)


def subscriber(id):
    with Redis(host="localhost", port=6379, db=0) as redis:
        while True:
            pubsub = redis.pubsub()
            pubsub.subscribe("channel")
            first = True
            for message in pubsub.listen():
                if first:
                    first = False
                    continue

                # data = int ( message["data"] )
                data = message["data"].decode()
                print(f"SUBSCRIBER{id} = {data}")


import threading

if __name__ == "__main__":
    for i in range(1):
        publisher_thread = threading.Thread(target=publisher, args=(i,))
        publisher_thread.start()

    for i in range(5):
        subscriber_thread = threading.Thread(target=subscriber, args=(i,))
        subscriber_thread.start()
