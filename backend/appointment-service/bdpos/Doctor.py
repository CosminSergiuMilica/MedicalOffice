from peewee import Model, CharField, IntegerField, Check

from .database import db


class Doctors(Model):
    id_doctor = IntegerField(primary_key=True)
    id_user = CharField(max_length=50, unique=True)
    last_name = CharField(max_length=50)
    first_name = CharField(max_length=50)
    email = CharField(max_length=70, unique=True)
    phone = CharField(max_length=10, constraints=[Check('phone REGEXP "^07[0-9]{8}$"')])
    specialization = CharField()
    class Meta:
        database = db
