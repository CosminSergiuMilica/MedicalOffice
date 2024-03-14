from peewee import *
from .database import db
class User(Model):
    id_user = CharField(max_length=50, primary_key=True)
    username = CharField(max_length=50, unique=True)
    password = CharField(max_length=255)
    tip = CharField(choices=['admin', 'patient', 'doctor'])
    secret = CharField(max_length=10)

    class Meta:
        database = db
        table_name = 'users'