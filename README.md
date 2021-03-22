## Playing with gRPC and Python

```protobuf
syntax = "proto3";
package api;

service Api {
  rpc sayHello (HelloRequest) returns (Hello) {}
  rpc getAll (ApiRequest) returns (api.Items) {}
  rpc getStream (ApiRequest) returns (stream api.Item) {}
}

message ApiRequest {
  int32 length = 1;
}

message Items {
  repeated api.Item items = 1;
}

message Item {
  int32 id = 1;
  string name = 2;
}

message HelloRequest {
  string name = 1;
}

message Hello {
  string message = 1;
}
```

```python
import grpc

from api_pb2 import Items, Item, Hello, HelloRequest, ApiRequest
from api_pb2_grpc import ApiServicer, ApiStub


class ApiServer(ApiServicer):
    def getAll(self, request, context):
        data = []
        for i in range(1, request.length + 1):
            data.append(Item(id=i, name=f'name {i}'))
        return Items(items=data)

    def getStream(self, request, context):
        for i in range(1, request.length + 1):
            yield Item(id=i, name=f'name {i}')

    def sayHello(self, request, context):
        return Hello(message=f'Hello {request.name}!')


class ApiClient:
    def __init__(self, target):
        channel = grpc.insecure_channel(target)
        self.client = ApiStub(channel)

    def sayHello(self, name):
        response = self.client.sayHello(HelloRequest(name=name))
        return response.message

    def getAll(self, length):
        response = self.client.getAll(ApiRequest(length=length))
        return response.items

    def getStream(self, length):
        response = self.client.getStream(ApiRequest(length=length))
        return response
```

```python
import logging
from concurrent import futures

import grpc

import settings
from api import ApiServer
from api_pb2_grpc import add_ApiServicer_to_server


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    add_ApiServicer_to_server(ApiServer(), server)
    server.add_insecure_port(f'[::]:{settings.BACKEND_PORT}')
    server.start()
    server.wait_for_termination()


if __name__ == '__main__':
    logging.basicConfig()
    serve()
```


```shell
python -m grpc_tools.protoc -I./protos --python_out=. --grpc_python_out=. ./protos/api.proto
```

```python
from flask import Flask, render_template

import settings
from api import ApiClient

app = Flask(__name__)

app.config["api"] = ApiClient(f"{settings.BACKEND_HOST}:{settings.BACKEND_PORT}")


@app.route("/")
def home():
    api = app.config["api"]
    return render_template(
        "index.html",
        name=api.sayHello("Gonzalo"),
        items=api.getAll(length=10),
        items2=api.getStream(length=5)
    )
```

```yaml
version: '3.6'

services:
  frontend:
    build:
      context: .
      dockerfile: Dockerfile
    environment:
      BACKEND_HOST: backend
    ports:
      - 5000:5000
    command: gunicorn -w 4 app:app -b 0.0.0.0:5000
  backend:
    build:
      context: .
      dockerfile: Dockerfile
    command: python server.py
```
