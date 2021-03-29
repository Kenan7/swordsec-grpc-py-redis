FROM python:3.8-slim

RUN mkdir /worker
WORKDIR /worker

COPY requirements.txt .
RUN pip install -r requirements.txt


COPY . .

ENTRYPOINT [ "python", "worker.py" ]
