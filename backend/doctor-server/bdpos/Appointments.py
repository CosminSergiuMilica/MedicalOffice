from peewee import Model, CharField, IntegerField, DateField, Check

from .database import db


class Appointments(Model):
    id_appointment = IntegerField(primary_key=True)
    id_doctor =CharField(max_length=50)
    id_patient = CharField(max_length=50)
    date = DateField()
    status = CharField(max_length=20, constraints=[Check('status IN ("onorata", "neprezentat", "anulat")')])
    class Meta:
        database = db
