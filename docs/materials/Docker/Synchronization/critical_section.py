from redis import Redis


def acquire_lock():
    with Redis(host="localhost", port=6379, db=0) as redis:
        while redis.setnx("lock", 1) == 0:
            pass


def release_lock():
    with Redis(host="localhost", port=6379, db=0) as redis:
        redis.delete("lock")


import time


def worker(id):
    while True:
        acquire_lock()
        print(f"WORKER{id} ENTER")
        time.sleep(1.5)
        print(f"WORKER{id} EXIT")
        release_lock()


import threading

if __name__ == "__main__":
    for i in range(5):
        worker_thread = threading.Thread(target=worker, args=(i,))
        worker_thread.start()
