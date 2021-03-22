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
