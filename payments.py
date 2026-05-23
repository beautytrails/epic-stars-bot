import requests
import logging
import uuid
from typing import Optional, Dict

from config import WATA_TOKEN

BASE_URL = "https://dg-api.wata.pro/api"
PRICE_PER_STAR = 1.4

async def create_payment_link(stars: int, telegram_user_id: int, username: str = None) -> Optional[Dict]:
    if not username:
        username = f"user_{telegram_user_id}"

    try:
        amount = round(stars * PRICE_PER_STAR, 2)
        # Самый простой orderId — WATA это любит
        order_id = f"sb{telegram_user_id}{stars}"

        payload = {
            "username": username,
            "count": stars,
            "amount": amount,
            "description": f"Покупка {stars} Telegram Stars",
            "orderId": order_id,
            "telegramId": str(telegram_user_id),
            "successRedirectUrl": "https://t.me/Epic_Stars_Gift_bot",
            "failRedirectUrl": "https://t.me/Epic_Stars_Gift_bot",
            "isTest": True
        }

        headers = {
            "Authorization": f"Bearer {WATA_TOKEN}",
            "Content-Type": "application/json"
        }

        response = requests.post(f"{BASE_URL}/stars", json=payload, headers=headers, timeout=15)

        logging.info(f"Статус WATA: {response.status_code}")
        logging.info(f"Ответ WATA: {response.text}")

        response.raise_for_status()
        data = response.json()

        if data.get("paymentLink"):
            logging.info(f"✅ Платёж создан успешно!")
            return {
                "paymentLink": data.get("paymentLink"),
                "orderId": order_id,
                "amount": amount,
                "stars": stars
            }
        else:
            logging.error(f"Нет paymentLink: {data}")
            return None

    except Exception as e:
        logging.error(f"❌ Ошибка создания платежа: {e}")
        return None