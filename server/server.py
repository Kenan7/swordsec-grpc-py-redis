import json
import random
from concurrent import futures
from datetime import datetime
from pprint import pprint as p
from typing import Dict

import grpc
from google.protobuf.json_format import MessageToDict, MessageToJson
from grpc_interceptor import ExceptionToStatusInterceptor
from grpc_interceptor.exceptions import NotFound
from redis import Redis
from rq import Queue

import users_pb2_grpc
from users_pb2 import UserResponse

redis_client = Redis(port=6379)

q = Queue(connection=redis_client)

class UsersService(users_pb2_grpc.UsersServicer):

    data = {}

    def process_incoming_request(self, _data):
        print(_data)
        self.data.update(
            MessageToDict(_data)
        )

    def write_to_json_file(self, file_name = 'default.json', _data = data):

        with open(file_name, 'w') as all_users_json_file:
            json.dump(_data, all_users_json_file)



    def SendUserInfo(self, request_iterator, context):
        q.enqueue(self.process_incoming_request, request_iterator)
        
    
    def SendUserInfoClientStream(self, request_iterator, context):

        for request in request_iterator:
            q.enqueue(self.process_incoming_request, request)

        try:
            q.enqueue(self.write_to_json_file, file_name='all_users.json')

            return UserResponse(status=True, message="ok")
        except:
            return UserResponse(status=False, message="not ok")




def serve():

    interceptors = [
        ExceptionToStatusInterceptor()
    ]

    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=10), 
        interceptors=interceptors
    )

    users_pb2_grpc.add_UsersServicer_to_server(
        UsersService(), server
    )
   
    server.add_insecure_port("127.0.0.1:50051")

    server.start()

    print("Listening...")

    server.wait_for_termination()


if __name__ == "__main__":
    serve()
