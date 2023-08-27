from db.init_db import User_Subscribes, Roles, db
from datetime import datetime


class SQLite():
    def __init__(self, connection):
        self.db = connection
        self.db.connect()

    def init_tables(self):
        self.db.create_tables([User_Subscribes, Roles])

    def add_role(self, role_name, role_id, price):
        Roles.create(role_name=role_name, role_id=role_id, price_rub=price).save()

    def remove_role(self, role_id):
        role = Roles.get(Roles.role_id == role_id)
        role.delete_instance()

    def get_saled_roles(self):
        query = Roles.select(Roles.role_name, Roles.price_rub, Roles.role_id).dicts()
        result = [role for role in query]
        return result

    def save_payment_info(self, data):
        user_subscribe = User_Subscribes.create(
            user_id=data['user_id'],
            role_name=data['role_name'],
            role_id=data['role_id'],
            cost=data['amount'],
            end_time=data['end_time']
        )
        user_subscribe.save()

    def select_overdue_subs(self):
        overdue_subs = User_Subscribes.select().where(User_Subscribes.end_time < datetime.now())
        deleted_subs = []
        for sub in overdue_subs:
            deleted_subs.append({
                'user_id': sub.user_id,
                'role_id': sub.role_id,
                'role_name': sub.role_name,
                'end_time': sub.end_time
            })
            sub.delete_instance()
        return deleted_subs

    def select_user_active_subs(self, user_id, role_id):
        user_active_subs = User_Subscribes.select().where(
            (User_Subscribes.user_id == user_id) &
            (User_Subscribes.role_id == role_id) &
            (User_Subscribes.end_time > datetime.now())
        )
        return user_active_subs

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.db.close()
