import time
from yookassa import Configuration, Payment
import uuid
from decimal import Decimal
from loguru import logger
from core.config import config
from init_bot import bot
from db.sqlite import SQLite
from db.init_db import db
from datetime import datetime, timedelta
import discord

Configuration.account_id = config.ACCOUNT_ID
Configuration.secret_key = config.SHOP_SECRET


async def check_payments(MAIN_GUILD):
    res = Payment.list()
    for transaction in res.items:
        if transaction.status == 'waiting_for_capture':
            user_id = transaction.description.split(",")[0].split("user_id:")[1]
            role_id = transaction.description.split(",")[1].split("role_id:")[1]
            role_name = transaction.description.split(",")[2].split("role_name:")[1]
            succeeded_transaction = {
                'id': transaction.id,
                'status': transaction.status,
                'amount': transaction.amount.value,
                'currency': transaction.amount.currency,
                'description': transaction.description,
                'created_at': transaction.created_at,
                'paid': transaction.paid,
                'user_id': user_id,
                'role_id': role_id,
                'role_name': role_name,
                'end_time': datetime.now() + timedelta(days=30)
            }
            logger.info(succeeded_transaction)
            idempotence_key = str(uuid.uuid4())
            Payment.capture(
                transaction.id,
                {
                    "amount": {
                        "value": str(transaction.amount.value.quantize(Decimal('1.00'))),
                        "currency": "RUB"
                    }
                },
                idempotence_key
            )
            user = await bot.fetch_user(int(user_id))
            emoji = '\U0001F389'
            await user.send(f"{user.mention}, Поздравляем! {emoji} \nВы успешно оплатили роль {role_name} на месяц!")

            with SQLite(db) as sqlite:
                sqlite.save_payment_info(succeeded_transaction)

            if MAIN_GUILD is not None:
                user = MAIN_GUILD.get_member(int(user_id))
                role = discord.utils.get(MAIN_GUILD.roles, id=int(role_id))
                if user and role:
                    await user.add_roles(role)  # Выдача роли пользователю
                    logger.info(f'Role {role.name} given to user {user.name}({user.id})')
                else:
                    logger.warning("User or role not found")
            else:
                logger.warning("Guild not found")


async def take_away_overdue_roles(MAIN_GUILD):
    with SQLite(db) as sqlite:
        overdue_subs = sqlite.select_overdue_subs()
        for sub in overdue_subs:
            user = MAIN_GUILD.get_member(int(sub["user_id"]))
            logger.info(f"Detected old role by user {sub['user_id']}")
            is_other_active_subs = sqlite.select_user_active_subs(sub["user_id"], sub['role_id'])
            if is_other_active_subs:
                logger.info(f"У пользователя {sub['user_id']} удалена 1 подписка, но у него есть более новая!")
                continue
            role = discord.utils.get(MAIN_GUILD.roles, id=int(sub["role_id"]))
            await user.remove_roles(role)
            message = f"{user.mention}, оплаченный срок твоей роли {sub['role_name']} на сервере {MAIN_GUILD.name} подошел к концу."
            user = await bot.fetch_user(int(sub["user_id"]))
            await user.send(message)
            logger.info(f"У пользователя {sub['user_id']} закончилась подписка на роль {sub['role_name']}")
