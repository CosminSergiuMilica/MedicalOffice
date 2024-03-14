from peewee import MySQLDatabase

db = MySQLDatabase(
    host='proiect-api-mysql-user-1',
    user='cosmin',
    password='cosmin',
    database='userdb',
    port=3306
)