import asyncio
import json
import logging as log
import os
import time
from pathlib import Path

import redis
from rq import Queue
from rq.job import Job

LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO').upper()
log.basicConfig(level=LOG_LEVEL)


listen = ['default']

REDIS_HOST = os.environ.get('REDIS_SERVER_ADDRESS', 'localhost')
REDIS_QUEUE = os.environ.get('REDIS_QUEUE', 'def')


connection = redis.Redis(
    host = REDIS_HOST,
    db=0
)

queue = Queue(name=REDIS_QUEUE, connection=connection)

current_file_path = f'{Path(__file__).resolve().parent}/users_final/data.json'

def file_operation(data):
    if Path(current_file_path).exists():
        try:
            with open(current_file_path, 'a+') as current_file:
                temp = json.load(current_file)

            temp.append(data)
        except Exception as e:
            print(e)
            temp = data


        with open(current_file_path, 'w') as current_file:
            current_file.write(
                json.dumps(temp, indent=4)
            )

    else:
        with open(current_file_path, 'w') as current_file:
            json.dump(current_file, data, indent=4)


def consume():
    log.info('consuming...')
    while True:
        finished_jobs = queue.finished_job_registry
        jobs_ids = finished_jobs.get_job_ids()
        jobs = Job.fetch_many(jobs_ids, connection=connection)

        list_of_data = []

        for job in jobs:
            try:
                list_of_data.append(job.return_value)
            except:
                pass

        file_operation(list_of_data)
            
        time.sleep(2) # interval for file save operation


if __name__ == '__main__':
    while True:
        consume()
