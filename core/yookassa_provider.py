from yookassa import Configuration, Payment
import uuid
from core.config import config
from decimal import Decimal


class Yookassa_Provider():
    def __init__(self):
        Configuration.account_id = config.ACCOUNT_ID
        Configuration.secret_key = config.SHOP_SECRET

    async def pay_request(self, user_id, role_id, role_name, price):
        idempotence_key = str(uuid.uuid4())
        payment = Payment.create({
            "amount": {
                "value": price + ".00",
                "currency": "RUB"
            },
            "payment_method_data": {
                "type": "bank_card"
            },
            "confirmation": {"type": "redirect", "return_url": "https://www.example.com/return_url"},
            "capture": False,
            "description": f"user_id:{user_id},role_id:{role_id},role_name:{role_name}"
        }, idempotence_key)

        confirmation_url = payment.confirmation.confirmation_url
        return confirmation_url
