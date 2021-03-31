FROM python:3.8-slim


RUN mkdir /service
WORKDIR /service/server


COPY requirements.txt .
RUN pip install -r requirements.txt


COPY . .

RUN python -m grpc_tools.protoc -I protobufs --python_out=. \
           --grpc_python_out=. protobufs/users.proto

EXPOSE 50051
ENTRYPOINT [ "python", "server.py" ]
