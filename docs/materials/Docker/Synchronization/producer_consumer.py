from redis import Redis


def produce(data):
    with Redis(host="localhost", port=6379, db=0) as redis:
        redis.lpush("buffer", data)


def consume():
    with Redis(host="localhost", port=6379, db=0) as redis:
        return redis.brpop("buffer")


import random
import time


def producer(id):
    while True:
        data = random.randint(0, 10)
        produce(data)
        print(f"PRODUCER{id} = {data}")
        time.sleep(1.5)


def consumer(id):
    while True:
        data = consume()
        print(f"CONSUMER{id} = {data}")
        time.sleep(1.5)


import threading

if __name__ == "__main__":
    for i in range(2):
        producer_thread = threading.Thread(target=producer, args=(i,))
        producer_thread.start()

    for i in range(5):
        consumer_thread = threading.Thread(target=consumer, args=(i,))
        consumer_thread.start()
