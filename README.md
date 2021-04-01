# SwordSec backend task

## Running the app

```bash
docker-compose up --build --scale rq-worker=5
```

## Protobufs

There are two methods in UsersService

- `SendUserInfo` (unary - unary)
    - we send and receive single request-response here

- `SendUserInfoClientStream` (stream - unary)
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


## Dockerfiles

I wanted to show how I customize dockerfile, 

typically, we see something like this in the blog posts, this is also a boilerplate that I took from the [RealPython](https://realpython.com/python-microservices-grpc/#docker)


but something can be optimized here.. 

why do we install the requirements after copying the content of the project?

this is the question I asked myself for the first time I saw this flow in tutorials (when I was learning django deployment for the first time)


if we modify even a letter in our project, we have to install all the requirements again because of this flow.

which is time consuming, also, docker built a cache system for us, so why don't we use it?


at least I did, here's how I customize the flow

#### the deafault dockerfile

```Dockerfile
FROM python:3.8-slim

RUN mkdir /service

# COPY protobufs/ /service/protobufs/
COPY . /service/client/

WORKDIR /service/client

RUN pip install -r requirements.txt
RUN python -m grpc_tools.protoc -I protobufs --python_out=. \
           --grpc_python_out=. protobufs/users.proto


EXPOSE 50051
ENTRYPOINT [ "python", "client.py" ]
```

#### customized dockerfile

```Dockerfile
...

RUN mkdir /service
WORKDIR /service/client


COPY requirements.txt .
RUN pip install -r requirements.txt


COPY . .

...
```

see? we copy the contents at the end, after installing the requirements. now even if our project content changes, we don't have to install all the requirements now,


actually we could've used that time to drink a coffee, soo no coffee for us now...


## Docker-compose

our [docker-compose](./docker-compose.yml) file is pretty straightforward actually, I just want to show the worker section to you.


I put two choices for us, either we can run the python worker module, which is runnig the redis queue worker at the core

OR

we can use (for whatever reason) docker image (hopefully from someone we trust) from the docker hub


```yml
worker:
    build: worker # ./worker
    networks:
        - microservices
    environment:
        - REDIS_HOST=redis
        - REDIS_PORT=6379
    depends_on:
        - server
        - redis

    #  OR 👇🏻

    rq-worker:
        image: jaredv/rq-docker:0.0.2
        command: rq worker -u redis://redis:6379 high normal low

        networks:
            - microservices

        depends_on:
            - redis

    rq-dashboard:
        image: jaredv/rq-docker:0.0.2 
        command: rq-dashboard -H rq-server
        ports:
        - 9181:9181
        
        networks:
            - microservices

        depends_on:
            - redis
```

I also added `rq-dashboard` in case we want to monitor our queue


Finally, I would like to explain how I built the service initalizing order. We don't want to start our redis server at the end, do we?


this is the order

- redis (server)
- gRPC server (depends on the redis server)
- gRPC client (depends on the gRPC server)
- python redis queue worker (depends on both server and redis)
- rq-dashboard (depends on the redis server)


In case you have questions about this project, reach me out [mirkanan.k@labrin.tech](mailto:mirkanan.k@labrin.tech)