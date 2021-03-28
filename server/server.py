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

redis_client = Redis(port=6333)

q = Queue(connection=redis_client)

class UsersService(users_pb2_grpc.UsersServicer):

    def SendUserInfo(self, request, context):
        # if request.category not in books_by_category:
        #     raise NotFound("Category not found")
        print('on func init')

        data = {}

        print('iter')
        
        print(request)

        data.update(MessageToDict(request))

        print('file open')
        try:
            with open(redis_client.get('current_file'), 'w') as all_users_json_file:
                json.dump(data, all_users_json_file)

            return UserResponse(status=True, message="ok")
        except:
            return UserResponse(status=False, message="not ok")




def serve():
    file_name = f'{datetime.now().strftime("%d %B, %Y - %H:%M:%S")}.json'
    
    redis_client.set('current_file', file_name)

    with open(file_name, 'w') as f:
        pass

    interceptors = [ExceptionToStatusInterceptor()]
    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=10), interceptors=interceptors
    )
    users_pb2_grpc.add_UsersServicer_to_server(
        UsersService(), server
    )
   
    server.add_insecure_port("[::]:50051")
    server.start()

    print("Listening...")
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
