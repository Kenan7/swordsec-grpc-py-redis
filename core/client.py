import json
import logging as log
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

log.basicConfig(level=log.DEBUG)

q = Queue(connection=Redis(port=6379))

users_host = os.getenv("USERS_HOST", "localhost")
users_channel = grpc.insecure_channel(f"{users_host}:50051")
users_client = UsersStub(users_channel)



def process_users_from_json_files():

    for json_file in Path('users').glob("*.json"):
        log.info(json_file)
        try:
            with open(json_file, 'r') as currently_opened_file:
                
                # code below will pass on from 6.json file
                json_content = json.load(currently_opened_file)
                
                for user in json_content:
                    try:
                        yield user
                    except:
                        continue
                
        except:
            continue                       

def client_stream():
    try:
        users_client.SendUserInfo(
            process_users_from_json_files()
        )

    except:
        pass


def main():
    log.info("Client initialized...")

    with grpc.insecure_channel("127.0.0.1:50051") as channel:
        stub = UsersStub(channel)

        for _user in process_users_from_json_files():

            try:
                user_response = stub.SendUserInfo(
                    UserRequest(**_user)
                )

                log.info(f"response (f server) | {user_response}")

            except:
                continue


if __name__ == "__main__":
    main()                  # unary - unary

    # client_stream()       # client stream - unary
