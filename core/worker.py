import os

import redis
from rq import Connection, Queue, Worker

listen = ['default']

redis_host = os.environ.get('REDIS_HOST', 'localhost')
redis_port = os.environ.get('REDIS_PORT', '6379')


conn = redis.Redis(
    host = redis_host,
    port = redis_port
)

conn = redis.Redis()

if __name__ == '__main__':
    with Connection(conn):
        
        worker = Worker(
            list(
                map(Queue, listen)
            )
        )
        worker.work()
