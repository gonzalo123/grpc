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
