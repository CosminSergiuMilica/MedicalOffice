# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc

import idmService_pb2 as idmService__pb2


class IDMServiceStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.Login = channel.unary_unary(
                '/IDMService/Login',
                request_serializer=idmService__pb2.LoginRequest.SerializeToString,
                response_deserializer=idmService__pb2.LoginResponse.FromString,
                )
        self.VerifyToken = channel.unary_unary(
                '/IDMService/VerifyToken',
                request_serializer=idmService__pb2.TokenRequest.SerializeToString,
                response_deserializer=idmService__pb2.TokenResponse.FromString,
                )
        self.SignUp = channel.unary_unary(
                '/IDMService/SignUp',
                request_serializer=idmService__pb2.SignUpRequest.SerializeToString,
                response_deserializer=idmService__pb2.SignUpResponse.FromString,
                )
        self.CreateDoctor = channel.unary_unary(
                '/IDMService/CreateDoctor',
                request_serializer=idmService__pb2.CreateDoctorRequest.SerializeToString,
                response_deserializer=idmService__pb2.CreateDoctorResponse.FromString,
                )
        self.DeleteUser = channel.unary_unary(
                '/IDMService/DeleteUser',
                request_serializer=idmService__pb2.DeleteUserRequest.SerializeToString,
                response_deserializer=idmService__pb2.DeleteUserResponse.FromString,
                )
        self.UpdateUser = channel.unary_unary(
                '/IDMService/UpdateUser',
                request_serializer=idmService__pb2.UpdateUserRequest.SerializeToString,
                response_deserializer=idmService__pb2.UpdateUserResponse.FromString,
                )


class IDMServiceServicer(object):
    """Missing associated documentation comment in .proto file."""

    def Login(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def VerifyToken(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def SignUp(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def CreateDoctor(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def DeleteUser(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def UpdateUser(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_IDMServiceServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'Login': grpc.unary_unary_rpc_method_handler(
                    servicer.Login,
                    request_deserializer=idmService__pb2.LoginRequest.FromString,
                    response_serializer=idmService__pb2.LoginResponse.SerializeToString,
            ),
            'VerifyToken': grpc.unary_unary_rpc_method_handler(
                    servicer.VerifyToken,
                    request_deserializer=idmService__pb2.TokenRequest.FromString,
                    response_serializer=idmService__pb2.TokenResponse.SerializeToString,
            ),
            'SignUp': grpc.unary_unary_rpc_method_handler(
                    servicer.SignUp,
                    request_deserializer=idmService__pb2.SignUpRequest.FromString,
                    response_serializer=idmService__pb2.SignUpResponse.SerializeToString,
            ),
            'CreateDoctor': grpc.unary_unary_rpc_method_handler(
                    servicer.CreateDoctor,
                    request_deserializer=idmService__pb2.CreateDoctorRequest.FromString,
                    response_serializer=idmService__pb2.CreateDoctorResponse.SerializeToString,
            ),
            'DeleteUser': grpc.unary_unary_rpc_method_handler(
                    servicer.DeleteUser,
                    request_deserializer=idmService__pb2.DeleteUserRequest.FromString,
                    response_serializer=idmService__pb2.DeleteUserResponse.SerializeToString,
            ),
            'UpdateUser': grpc.unary_unary_rpc_method_handler(
                    servicer.UpdateUser,
                    request_deserializer=idmService__pb2.UpdateUserRequest.FromString,
                    response_serializer=idmService__pb2.UpdateUserResponse.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'IDMService', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class IDMService(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def Login(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/IDMService/Login',
            idmService__pb2.LoginRequest.SerializeToString,
            idmService__pb2.LoginResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def VerifyToken(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/IDMService/VerifyToken',
            idmService__pb2.TokenRequest.SerializeToString,
            idmService__pb2.TokenResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def SignUp(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/IDMService/SignUp',
            idmService__pb2.SignUpRequest.SerializeToString,
            idmService__pb2.SignUpResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def CreateDoctor(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/IDMService/CreateDoctor',
            idmService__pb2.CreateDoctorRequest.SerializeToString,
            idmService__pb2.CreateDoctorResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def DeleteUser(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/IDMService/DeleteUser',
            idmService__pb2.DeleteUserRequest.SerializeToString,
            idmService__pb2.DeleteUserResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def UpdateUser(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/IDMService/UpdateUser',
            idmService__pb2.UpdateUserRequest.SerializeToString,
            idmService__pb2.UpdateUserResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)
