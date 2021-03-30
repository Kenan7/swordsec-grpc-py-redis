# SwordSec backend task

## Protobufs

There are two methods in UsersService

- SendUserInfo (unary - unary)
    - we send and receive single request-response here

- SendUserInfoClientStream (stream - unary)
    - we send multiple requests and receive single response form the server


```proto
service Users {
    rpc SendUserInfo (UserRequest) returns (UserResponse);
    rpc SendUserInfoClientStream (stream UserRequest) returns (UserResponse);
}
```


I thought client stream is also applicable in our case. That's why I also included it.


Client stream generates stream of requests and when finished generating, server sends back one response for all the requests


Considering we need to send users to be processed in the server, we can generate and stream the users and get the response if it was ok.


## Client

This is where we generate requests
```py
def process_users_from_json_files():
    ...
    for user in json_content:
        yield UserRequest(**user)
    ...
```

and we send the generated requests to the server
```py
def client_stream():
    users_client.SendUserInfo(
        process_users_from_json_files()
    )
```

Client stream is awesome and all, but I actually used unary-unary method, meaning, I sent one user to the server to be processed and got one response for that user.

this is how my `main()` function looks like

```py
def main():
    log.info("Client initialized...")
    for _user in process_users_from_json_files():
        ...
            user_response = users_client.SendUserInfo(
                _user
            )
        ...
```

I think both of them are okay, I just wanted to demonstrate that we can do whichever we want for the needs of the project.


## Server

This section demonstrates how our server handles the requests

`process_incoming_request()` function is queued when we receive a request

```py
def process_incoming_request(self, _data):

    self.data.update(
        MessageToDict(_data)
    )

    return UserResponse(status=True, message="ok")
```

here, our method receives the request and queues the function to incoming data

```py
def SendUserInfo(self, request, context):
    log.info(f'incoming request -> {request}')
    q.enqueue(self.process_incoming_request, request)
```

for the client stream, we use `request_iterator` instead of `request` because since it will be a stream from the client, we'll get multiple requests to handle.

we'll loop through the `request_iterator`

```py
def SendUserInfoClientStream(self, request_iterator, context):

    for request in request_iterator:
        log.info(f'incoming request (client stream) -> {request}')

        q.enqueue(self.process_incoming_request, request)

    try:
        q.enqueue(self.write_to_json_file, file_name='all_users.json')

        return UserResponse(status=True, message="ok")
    except:
        return UserResponse(status=False, message="not ok")
```

after we queue the stream, we also can add the `write_to_json_file()` function to queue to save all the data to the json file.


I spesifically used queue for this function, because the time we are on the write_to_json_file() line, there is a possibility that we haven't processed the requests yet, so we make sure this function executes last by adding it to the queue.