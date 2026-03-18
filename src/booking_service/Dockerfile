FROM python:latest

RUN apt-get update && apt-get install -y protobuf-compiler
RUN pip install fastapi uvicorn grpcio grpcio-tools psycopg2-binary
RUN mkdir -p /protos

COPY --from=flight_service contract.proto ./raw_protos/

RUN protoc -I=./raw_protos --python_out=./protos ./raw_protos/*.proto
RUN python -m grpc_tools.protoc -I=./raw_protos --python_out=./protos --grpc_python_out=./protos ./raw_protos/*.proto

ENV PYTHONPATH="/protos:${PYTHONPATH}"

COPY main.py .

EXPOSE 80

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]
