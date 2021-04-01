FROM python:3.8-slim


RUN mkdir /service
WORKDIR /service/consumer


COPY requirements.txt .
RUN pip install -r requirements.txt


COPY . .

EXPOSE 50051
ENTRYPOINT [ "python", "consumer.py" ]
