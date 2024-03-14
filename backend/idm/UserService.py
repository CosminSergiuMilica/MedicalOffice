import datetime
import logging

from peewee import IntegrityError
import grpc
from grpc import *
from concurrent import futures
import time
import uuid
import bcrypt
import jwt


import idmService_pb2
import idmService_pb2_grpc
from user.users import User
from user.database import db
def check_password(password, hashed_password):
    return bcrypt.checkpw(password.encode(), hashed_password)
def connect_database():
    if db.is_closed():
        try:
            db.connect()
        except ConnectionError as e:
            print(e)

def close_database():
    if not db.is_closed():
        db.close()

SECRET_KEY = "GoSdJgsDEe343"
class UserService(idmService_pb2_grpc.IDMServiceServicer):
    def Login(self, request, context):
        username = request.username
        password = request.password
        user = User.get_or_none(User.username == username)
        if user is not None:
            if bcrypt.checkpw(password.encode(), user.password.encode()):
                payload = {
                    'iss': "http://proiect-api-users-service-1:50051/Login",
                    'username': username,
                    'role': user.tip,
                    'sub': str(user.id_user),
                    'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=2),
                    'jti': str(uuid.uuid4())
                }
                jwt_token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
                return idmService_pb2.LoginResponse(
                    access_token=str(jwt_token),
                    message="Autentificare cu succes",
                    code=200
                )
            else:
                print("Parola incorecta")
                return idmService_pb2.LoginResponse(access_token=None,
                                                    message="Autentificare eșuata:  parola incorecte",
                                                    code=401)
        else:
            print("User incorect")
            return idmService_pb2.LoginResponse(access_token=None,
                                                message="Autentificare eșuata: Utilizator  incorecte",
                                                code=401)


    def VerifyToken(self, request, context):
        jwt_token = request.token
        try:
            decoded_token = jwt.decode(jwt_token, SECRET_KEY, algorithms=['HS256'])
            username = decoded_token.get('username')

            return idmService_pb2.TokenResponse(
                message="Tokenul JWT este valid si autentic",
                is_valid='valid'
            )
        except jwt.ExpiredSignatureError:
            return idmService_pb2.TokenResponse(
                message="Tokenul JWT a expirat",
                is_valid='invalid'
            )
        except jwt.InvalidTokenError:
            return idmService_pb2.TokenResponse(
                message="Tokenul JWT este invalid sau corupt",
                is_valid='invalid'
            )

    def SignUp(self, request, context):
        username = request.username
        password = request.password
        user_type = 'patient'
        user_secret = bcrypt.gensalt()
        hash_password = bcrypt.hashpw(password.encode(), user_secret)
        try:
            user_id = uuid.uuid4()
            payload = {
                'iss': "http://proiect-api-users-service-1:50051/SignUp",
                'username': username,
                'role': user_type,
                'sub': str(user_id),
                'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=2),
                'jti': str(uuid.uuid4())
            }
            jwt_token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
            print(jwt_token)
            if jwt_token:
                with db.atomic() as transaction:
                    new_user = User.create(
                        id_user=user_id,
                        username = username,
                        password=hash_password,
                        tip = user_type,
                        secret= user_secret
                    )
            return idmService_pb2.SignUpResponse(
                access_token=str(jwt_token),
                id_user=str(user_id),
                message='Utilizator inregistrat cu succes',
                code=201
            )
        except IntegrityError as e:
            transaction.rollback()
            return idmService_pb2.SignUpResponse(message=f"Eroare la inregistrare", code=409)


    def DeleteUser(self, request, context):
        id_user = request.user_id
        try:
            with db.atomic():
                user = User.get_or_none(User.id_user == id_user)
                if user is None:
                    return idmService_pb2.DeleteUserResponse(message=f"Userul {id_user} nu exista", code=404)
                user.delete_instance()
                return idmService_pb2.DeleteUserResponse(message=f"User sters cu succes", code=204)
        except IntegrityError as e:
            return idmService_pb2.SignUpResponse(
                message=str(e),
                code=409
            )
        except Exception as e:
            return idmService_pb2.DeleteUserResponse(message=f"Eroare la inregistrare: {str(e)}", code=500)

    def CreateDoctor(self, request, context):
        username = request.username
        password = request.password
        user_type = 'doctor'
        user_secret = bcrypt.gensalt()
        hash_password = bcrypt.hashpw(password.encode(), user_secret)

        try:
            user_id = uuid.uuid4()
            with db.atomic() as transaction:
                new_user = User.create(
                    id_user=user_id,
                    username=username,
                    password=hash_password,
                    tip=user_type,
                    secret=user_secret
                )

            return idmService_pb2.CreateDoctorResponse(
                message='Utilizator inregistrat cu succes',
                id_user=str(user_id)
            )
        except IntegrityError as ie:
            transaction.rollback()
            logging.error(f"Eroare de integritate: {str(ie)}")
            return idmService_pb2.CreateDoctorResponse(
                message=f"Eroare la inregistrare: {str(ie)}",
                id_user="NONE",
                code=409
            )


    def UpdateUser(self, request, context):
        username = request.username
        password = request.password
        id_user = request.id_user

        try:
            user = User.get(User.id_user==id_user)
            user.username = username
            user.password = password
            user.save()
            return idmService_pb2.UpdateUserResponse(id_user=id_user, message="User actualizat cu succes", code=200)
        except User.DoesNotExist:
            return idmService_pb2.UpdateUserResponse(message="Userul nu a fost gasit", code=404)

    def GetSecret(self, request, context):
        username = request.username
        try:
            user = User.get(User.username == username)
            secret = user.secret
            return idmService_pb2.SecretResponse(secret=secret)
        except User.DoesNotExist:
            return idmService_pb2.SecretResponse(secret="")

server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
idmService_pb2_grpc.add_IDMServiceServicer_to_server(UserService(), server)
server.add_insecure_port('[::]:50051')

print('Conectarea la baza de date...')
connect_database()

print('Pornirea serverului gRPC...')
server.start()

try:
    while True:
        time.sleep(86400)
except KeyboardInterrupt:
    print('oprim server...')
finally:
    print('inchiderea conexiunii la baza de date...')
    close_database()
    server.stop(0)
