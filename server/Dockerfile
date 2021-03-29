FROM python:3.8-slim


RUN mkdir /service
# COPY protobufs/ /service/protobufs/
COPY . /service/server/

WORKDIR /service/server
RUN pip install -r requirements.txt


RUN python -m grpc_tools.protoc -I protobufs --python_out=. \
           --grpc_python_out=. protobufs/users.proto

EXPOSE 50051
ENTRYPOINT [ "python", "server.py" ]
