import asyncio
import logging
import os
import uuid
import requests
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv

load_dotenv()

bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()

WATA_TOKEN = os.getenv("PAYMENT_TOKEN")
BOT_USERNAME = "Epic_Stars_Gift_bot"

# ================== FSM ==================
class StarsStates(StatesGroup):
    waiting_username = State()
    waiting_amount = State()

# ================== КЛАВИАТУРЫ ==================
def main_menu():
    kb = [
        [InlineKeyboardButton(text="⭐ Купить Звезды", callback_data="buy_stars")],
        [InlineKeyboardButton(text="💎 Телеграм Премиум", callback_data="buy_premium")],
        [InlineKeyboardButton(text="❤️ Наши отзывы", callback_data="reviews")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def stars_presets(username: str):
    kb = [
        [
            InlineKeyboardButton(text="50 ⭐", callback_data="stars_preset_50"),
            InlineKeyboardButton(text="100 ⭐", callback_data="stars_preset_100"),
            InlineKeyboardButton(text="500 ⭐", callback_data="stars_preset_500")
        ],
        [
            InlineKeyboardButton(text="1000 ⭐", callback_data="stars_preset_1000"),
            InlineKeyboardButton(text="5000 ⭐", callback_data="stars_preset_5000")
        ],
        [InlineKeyboardButton(text="3000 ⭐", callback_data="stars_preset_3000")],
        [InlineKeyboardButton(text="😀 Купить Другу", callback_data="stars_friend")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def premium_menu():
    kb = [
        [
            InlineKeyboardButton(text="⭐ 3 Месяца", callback_data="premium_3"),
            InlineKeyboardButton(text="⭐ 6 Месяцев", callback_data="premium_6")
        ],
        [InlineKeyboardButton(text="⭐ 1 Год", callback_data="premium_12")],
        [InlineKeyboardButton(text="😀 Купить Другу", callback_data="premium_friend")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

# ================== STARS (работает) ==================
def get_star_price(username: str):
    url = f"https://dg-api.wata.pro/api/stars/price?Username={username.strip('@')}"
    headers = {"Authorization": f"Bearer {WATA_TOKEN}"}
    try:
        r = requests.get(url, headers=headers, timeout=15)
        r.raise_for_status()
        return r.json().get("minPrice", 1.5)
    except:
        return 1.5

def create_stars_order(username: str, count: int, amount: float):
    url = "https://dg-api.wata.pro/api/stars"
    headers = {"Authorization": f"Bearer {WATA_TOKEN}", "Content-Type": "application/json"}
    payload = {
        "username": username.strip("@"),
        "count": count,
        "amount": round(amount, 2),
        "description": f"Покупка {count} ⭐ для {username}",
        "orderId": str(uuid.uuid4()),
        "successRedirectUrl": f"https://t.me/Epic_Stars_Gift_bot",
        "failRedirectUrl": f"https://t.me/Epic_Stars_Gift_bot"
    }
    try:
        r = requests.post(url, json=payload, headers=headers, timeout=30)
        r.raise_for_status()
        return r.json().get("paymentLink")
    except Exception as e:
        logging.error(f"Stars error: {e}")
        return None

# ================== PREMIUM H2H — ИСПРАВЛЕНО ПО ДОКУМЕНТАЦИИ ==================
def create_premium_payment(username: str, months: int, price: int):
    url = "https://api.wata.pro/api/h2h/links"
    headers = {
        "Authorization": f"Bearer {WATA_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "amount": float(price),                    # строго float как в примере документации
        "currency": "RUB",
        "description": f"Telegram Premium {months} мес. для @{username}",
        "orderId": str(uuid.uuid4()),
        "successRedirectUrl": f"https://t.me/Epic_Stars_Gift_bot",
        "failRedirectUrl": f"https://t.me/Epic_Stars_Gift_bot"
    }
    try:
        r = requests.post(url, json=payload, headers=headers, timeout=30)
        r.raise_for_status()
        data = r.json()
        return data.get("link") or data.get("paymentLink") or data.get("url")
    except Exception as e:
        error_text = r.text if 'r' in locals() else "No response"
        logging.error(f"Premium H2H error: {e} | Response: {error_text} | Payload: {payload}")
        return None

# ================== ХЭНДЛЕРЫ ==================
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "👋 <b>Добро пожаловать в StarBuy!</b>\n\n"
        "Здесь можно приобрести Telegram звезды быстро, безопасно а главное - дешево!\n\n"
        "☺️ Чтобы продолжить, просто нажмите нужную вам кнопку ниже!",
        parse_mode="HTML",
        reply_markup=main_menu()
    )

@dp.callback_query(F.data == "buy_stars")
async def buy_stars(callback: types.CallbackQuery):
    username = callback.from_user.username or f"id{callback.from_user.id}"
    await callback.message.edit_text(
        f"⭐️ <b>Введите нужное количество звезд (50 - 1000000)</b>\n\n"
        f"👤 Покупка для: @{username}",
        parse_mode="HTML",
        reply_markup=stars_presets(username)
    )

@dp.callback_query(F.data.startswith("stars_preset_"))
async def stars_preset_selected(callback: types.CallbackQuery):
    count = int(callback.data.split("_")[-1])
    username = callback.from_user.username or f"id{callback.from_user.id}"
    min_price = get_star_price(username)
    amount = round(min_price * count, 2)
    payment_link = create_stars_order(username, count, amount)

    if payment_link:
        await callback.message.edit_text(
            f"✅ <b>Заказ на {count} ⭐ создан!</b>\n\n"
            f"👤 Получатель: @{username}\n"
            f"💰 Сумма: {amount} ₽\n\n"
            f"🔗 <b>Платёжная ссылка:</b>\n{payment_link}\n\n"
            f"После оплаты звёзды придут автоматически.",
            parse_mode="HTML",
            disable_web_page_preview=True
        )
    else:
        await callback.message.edit_text("❌ Ошибка создания платежа.")

@dp.callback_query(F.data == "stars_friend")
async def stars_buy_for_friend(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("👤 Введите username получателя (с @ или без):")
    await state.set_state(StarsStates.waiting_username)

@dp.message(StarsStates.waiting_username)
async def get_friend_username(message: types.Message, state: FSMContext):
    username = message.text.strip()
    await state.update_data(username=username)
    await message.answer(f"⭐️ Покупка для @{username}\n\nВведите количество звёзд (50-1000000):")
    await state.set_state(StarsStates.waiting_amount)

# ================== PREMIUM ==================
@dp.callback_query(F.data == "buy_premium")
async def buy_premium(callback: types.CallbackQuery):
    username = callback.from_user.username or f"id{callback.from_user.id}"
    await callback.message.edit_text(
        f"💎 <b>Premium для @{username}</b>\n\n"
        f"Выберите срок подписки:",
        parse_mode="HTML",
        reply_markup=premium_menu()
    )

@dp.callback_query(F.data.startswith("premium_"))
async def premium_selected(callback: types.CallbackQuery):
    data_map = {
        "3": (3, 1120, "3 месяца"),
        "6": (6, 1490, "6 месяцев"),
        "12": (12, 2700, "1 год")
    }
    months, price, text_months = data_map.get(callback.data.split("_")[1], (3, 1120, "3 месяца"))
    username = callback.from_user.username or f"id{callback.from_user.id}"

    await callback.message.edit_text(
        f"⭐ <b>Оплата Telegram Premium</b>\n\n"
        f"Аккаунт: @{username}\n"
        f"Срок: {text_months}\n"
        f"Сумма: <b>{price} ₽</b>\n\n"
        f"⏳ Счет действителен 90 минут.\n\n"
        f"⚠️ <b>Оплачивая, вы подтверждаете, что покупаете Telegram Premium</b> "
        f"для себя или в подарок своим знакомым, и НЕ оплачиваете товары на других сайтах/сервисах "
        f"в пользу незнакомых лиц!",
        parse_mode="HTML"
    )

    payment_link = create_premium_payment(username, months, price)

    if payment_link:
        await callback.message.answer(
            f"🔗 <b>Платёжная ссылка:</b>\n{payment_link}\n\n"
            f"После оплаты Premium активируется автоматически.",
            parse_mode="HTML",
            disable_web_page_preview=True
        )
    else:
        await callback.message.answer("❌ Ошибка создания платежа.\n\nПопробуйте позже или напишите в поддержку.")

@dp.callback_query(F.data == "reviews")
async def show_reviews(callback: types.CallbackQuery):
    await callback.message.edit_text("❤️ Наши отзывы\n\nВставь сюда ссылку на канал с отзывами.")

# ================== ЗАПУСК ==================
async def main():
    logging.basicConfig(level=logging.INFO)
    print("🤖 Бот StarBuy запущен! (H2H Premium — исправлено по документации)")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())