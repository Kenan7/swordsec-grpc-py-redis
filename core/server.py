import json
import logging as log
import os
from concurrent import futures
from pprint import pprint as p
from typing import Dict

import grpc
from google.protobuf.json_format import MessageToDict, MessageToJson
from grpc_interceptor import ExceptionToStatusInterceptor
from redis import Redis
from rq import Queue

from tasks import process_incoming_request
from users_pb2 import UserResponse
from users_pb2_grpc import UsersServicer, add_UsersServicer_to_server

LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO').upper()
log.basicConfig(level=LOG_LEVEL)


SERVER_ADDRESS = f"{os.environ.get('GRPC_SERVER_ADDRESS', 'localhost')}:23333"
REDIS_HOST = os.environ.get('REDIS_SERVER_ADDRESS', 'localhost')
REDIS_QUEUE = os.environ.get('REDIS_QUEUE', 'def')

print(REDIS_HOST)
print(REDIS_QUEUE)

q = Queue(
    name=REDIS_QUEUE,
    connection=Redis(
        host=REDIS_HOST,
        db=0
    )
)


from icecream import ic


class UsersService(UsersServicer):


    def write_to_json_file(self, file_name = 'default.json', _data = {}):

        with open(file_name, 'w') as all_users_json_file:

            json.dump(_data, all_users_json_file)



    def SendUserInfo(self, request, context):
        log.info(f'''

            incoming request -> {request}
            
        ''')

        try:
            job = q.enqueue('tasks.process_incoming_request', MessageToDict(request))
            
            return UserResponse(status=True, message="ok")

        except Exception as e:
            return UserResponse(status=False, message=e)
        
    
    def SendUserInfoClientStream(self, request_iterator, context):

        try:

            for request in request_iterator:
                log.info(f'incoming request (client stream) -> {request}')

                job = q.enqueue('tasks.process_incoming_request',  MessageToDict(request))

            # q.enqueue(self.write_to_json_file, file_name='all_users.json')
            
            return UserResponse(status=True, message="ok")

        except:
            return UserResponse(status=False, message="not ok")
            



def serve():

    interceptors = [
        ExceptionToStatusInterceptor()
    ]

    server = grpc.server(
        futures.ThreadPoolExecutor(), 
        interceptors=interceptors
    )

    add_UsersServicer_to_server(
        UsersService(), server
    )
   
    server.add_insecure_port(SERVER_ADDRESS)

    log.info(f"Server is listening on {SERVER_ADDRESS}")

    server.start()


    server.wait_for_termination()


if __name__ == "__main__":
    serve()
