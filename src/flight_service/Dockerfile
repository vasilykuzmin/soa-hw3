FROM python:latest

WORKDIR /service

RUN apt-get update && apt-get install -y protobuf-compiler
RUN pip install grpcio-tools psycopg2-binary
RUN mkdir -p /service/protos

COPY contract.proto ./raw_protos/

RUN protoc -I=./raw_protos --python_out=./protos ./raw_protos/*.proto
RUN python -m grpc_tools.protoc -I=./raw_protos --python_out=./protos --grpc_python_out=./protos ./raw_protos/*.proto

ENV PYTHONPATH="/service/protos:${PYTHONPATH}"

COPY main.py .

CMD ["python", "/service/main.py"]
