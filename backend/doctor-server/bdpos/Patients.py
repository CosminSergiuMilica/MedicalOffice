from peewee import Model, CharField, IntegerField, DateField, BooleanField, Check

from .database import db


class Patients(Model):
    cnp = CharField(primary_key=True, max_length=13)
    id_user = CharField(max_length=50, unique=True)
    last_name = CharField(max_length=50)
    first_name = CharField(max_length=50)
    email = CharField(max_length=70, unique=True)
    phone = CharField(max_length=10, constraints=[Check('phone REGEXP "^07[0-9]{8}$"')])
    birth_date = DateField()
    is_active = BooleanField()

    class Meta:
        database = db
