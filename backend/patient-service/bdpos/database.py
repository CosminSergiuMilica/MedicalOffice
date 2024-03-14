from peewee import MySQLDatabase

db = MySQLDatabase(
    host='proiect-api-mariadb-1',
    user='cosmin',
    password='cosmin',
    database='pos-bd'
)
