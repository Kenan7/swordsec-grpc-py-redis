import json
import os
import time
from glob import glob
from pathlib import Path
from pprint import pprint as p

import grpc
from google.protobuf.json_format import MessageToDict, MessageToJson
from redis import Redis
from rq import Queue

from users_pb2 import UserRequest, UserResponse
from users_pb2_grpc import UsersStub

q = Queue(connection=Redis(port=6333))

users_host = os.getenv("USERS_HOST", "localhost")
users_channel = grpc.insecure_channel(f"{users_host}:50051")
users_client = UsersStub(users_channel)



def process_users_from_json_files():

    for json_file in Path('users').glob("*.json"):

        with open(json_file, 'r') as currently_opened_file:

            try:
                json_content = json.load(currently_opened_file)
                
                for user in json_content:
                        yield user
            except:
                continue
def main():
    # with grpc.insecure_channel('localhost:50051') as channel:
    for _user in process_users_from_json_files():

        try:
            request_to_remote = UserRequest(**_user)

            p(f'client | req -> {request_to_remote} (type) -> {type(request_to_remote)}')

            user_response = users_client.SendUserInfo(
                request_to_remote
            )

            p(f'client | response -> {user_response}')
        except:
            continue



        # print("Greeter client received: " + response.message)

if __name__ == "__main__":
    main()
