import json
import logging as log
import os
import time
from glob import glob
from pathlib import Path
from pprint import pprint as p

import grpc
from google.protobuf.json_format import MessageToDict, MessageToJson

from users_pb2 import UserRequest, UserResponse
from users_pb2_grpc import UsersStub

log.basicConfig(level=log.DEBUG)


SERVER_ADDRESS = f"{os.environ.get('GRPC_SERVER_ADDRESS', 'localhost')}:23333"




def process_users_from_json_files():

    for json_file in Path('users').glob("*.json"):

        log.info(f'''

            Processing the {json_file}...

        ''')

        try:
            with open(json_file, 'r') as currently_opened_file:
                
                # code below will pass on from 6.json file
                json_content = json.load(currently_opened_file)
                
                for user in json_content:
                    try:
                        yield UserRequest(**user)
                    except:
                        continue
                
        except Exception as e:
            log.error(f'''

                Could not process the file {json_file} -> {e}
                
            ''')
            continue                       

def client_stream():
    with grpc.insecure_channel(SERVER_ADDRESS, options=(('grpc.enable_http_proxy', 0),)) as channel:
        try:
            stub = UsersStub(channel)

            stub.SendUserInfo(
                process_users_from_json_files()
            )

        except:
            pass


def main():
    log.info("Client initialized...")
                                                  # thank you https://stackoverflow.com/a/63580067/10264246
    with grpc.insecure_channel(SERVER_ADDRESS, options=(('grpc.enable_http_proxy', 0),)) as channel:

        stub = UsersStub(channel)

        for _user in process_users_from_json_files():
            # time.sleep(1)           #  you may want to enable sleep to monitor logs
            try:
                log.info(f'''

                    Sending data to the server -> {_user}
                    
                ''')

                user_response = stub.SendUserInfo(_user)


                log.info(f'''
                
                    Received from the server -> {user_response}
                
                ''')

            except Exception as e:
                log.error(f'''
                    Could not send the data -> {e}
                    
                    Continuing...
                ''')

                continue


if __name__ == "__main__":
    main()                  # unary - unary

    # client_stream()       # client stream - unary
