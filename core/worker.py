import logging as log
import os

from redis import Redis
from rq import Connection, Queue, Worker

LOG_LEVEL = os.environ.get('LOG_LEVEL', 'DEBUG').upper()
log.basicConfig(level=LOG_LEVEL)

REDIS_HOST = os.environ.get('REDIS_SERVER_ADDRESS', 'localhost')
REDIS_QUEUE = os.environ.get('REDIS_QUEUE', 'def')

listen = ['high', 'default', 'low']

connection = Redis(
        host=REDIS_HOST,
        db=0
    )

if __name__ == '__main__':
    with Connection(connection):
        worker = Worker(map(Queue, listen))
        worker.work()
        # log.info(f'''
        
        #         WORKER: {(worker)}
        
        # ''')


