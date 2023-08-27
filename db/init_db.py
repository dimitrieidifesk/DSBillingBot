from datetime import datetime
from peewee import *

db = SqliteDatabase('main_database.db')


class User_Subscribes(Model):
    id = PrimaryKeyField()
    user_id = TextField()
    role_name = TextField()
    role_id = TextField()
    cost = TextField()
    start_time = DateTimeField(default=datetime.now)
    end_time = DateTimeField()

    class Meta:
        database = db


class Roles(Model):
    id = PrimaryKeyField()
    role_name = TextField()
    role_id = TextField()
    price_rub = TextField()
    created_at = DateTimeField(default=datetime.now)

    class Meta:
        database = db
