## Playing with gRPC and Python

When we work with microservices normally we need to have, in one way or another, something to communicate between them. Basically we have two choices: Synchronous (APIs) and asynchronous communications (message queues). REST APIs are a pretty straightforward way to create a communication channel. We've a lot of frameworks and microframeworks to create REST APIs. For example, in Python, we can use Flask. REST is simple, and it can fit in a lot of cases but sometimes is not enough. REST API is a HTTP service and HTTP is a protocol built over TCP. When we create a REST connection we're opening a TCP connection to the server, we send the request payload, we receive the response, and we close the connection. If we need to perform a lot of connections maybe we can face a bottleneck. Also we have the payload. We need to define how we're going to encode the information. We normally use JSON (we also can use XML). It's easy to encode/decode JSON in almost all languages but JSON is plain text. Big payloads over TCP connection means slow response time.

To solve this situation we've another tool in our toolbox. This tool is [gRPC](https://grpc.io/). With gRPC we create a persistent connection between client and server (instead of open and close connection like REST) and also we use a binary payload to reduce the size improving the performance. 

First we need to define the protocol we're going to use. It's something that we don't need to do in with HTTP APIs (we use JSON and we forget the rest). It's an extra step. Not complicated, but an extra. We need to define the types of our service and variables using a proto file.

```protobuf
// api.proto
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

With our proto file (language agnostic) we can create a the wrapper of our service using our programming language. In my case python:

```shell
python -m grpc_tools.protoc -I./protos --python_out=. --grpc_python_out=. ./protos/api.proto
```

Of course we can create clients using one language and servers using another. Both using the same proto file.

It creates two files. We don't need to open those files. We'll import those files to create our client and server. We can use those files directly but I preffer to use an extra wrapper. Without reinventing the wheel only to make me easy to use the client/and server.

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

Now I can create a server.
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


And also a client. In my example I'm going to use a flask frontend that consumes the gRPC server
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

We can deploy the example in a docker server. Here the docker-compose.yml
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
