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
REVIEWS_LINK = "https://t.me/+gP1By9vW8PJmMzYy"

# ================== FSM ==================
class StarsStates(StatesGroup):
    waiting_username = State()
    waiting_amount = State()

class PremiumStates(StatesGroup):
    waiting_username = State()


# ================== КЛАВИАТУРЫ ==================

def main_menu():
    kb = [
        [InlineKeyboardButton(text="⭐ Купить Звезды", callback_data="buy_stars")],
        [InlineKeyboardButton(text="💎 Телеграм Премиум", callback_data="buy_premium")],
        [InlineKeyboardButton(text="❤️ Наши отзывы", url=REVIEWS_LINK)],
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)


def stars_menu():
    kb = [
        [
            InlineKeyboardButton(text="⭐ 50", callback_data="stars_preset_50"),
            InlineKeyboardButton(text="⭐ 100", callback_data="stars_preset_100"),
            InlineKeyboardButton(text="⭐ 500", callback_data="stars_preset_500"),
        ],
        [
            InlineKeyboardButton(text="⭐ 1 000", callback_data="stars_preset_1000"),
            InlineKeyboardButton(text="⭐ 5 000", callback_data="stars_preset_5000"),
        ],
        [InlineKeyboardButton(text="😍 Купить Другу", callback_data="stars_friend")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)


def premium_menu():
    kb = [
        [
            InlineKeyboardButton(text="⭐ 3 Месяца", callback_data="premium_3"),
            InlineKeyboardButton(text="⭐ 6 Месяцев", callback_data="premium_6"),
        ],
        [InlineKeyboardButton(text="⭐ 1 Год", callback_data="premium_12")],
        [InlineKeyboardButton(text="😍 Купить Другу", callback_data="premium_friend")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)


def cancel_kb():
    kb = [[InlineKeyboardButton(text="❌ Отменить", callback_data="cancel")]]
    return InlineKeyboardMarkup(inline_keyboard=kb)


def back_to_main():
    kb = [[InlineKeyboardButton(text="◀️ Главное меню", callback_data="main_menu")]]
    return InlineKeyboardMarkup(inline_keyboard=kb)


# ================== WATA API ==================

def get_star_price(username: str) -> float:
    url = f"https://dg-api.wata.pro/api/stars/price?Username={username.strip('@')}"
    headers = {"Authorization": f"Bearer {WATA_TOKEN}"}
    try:
        r = requests.get(url, headers=headers, timeout=15)
        r.raise_for_status()
        return r.json().get("minPrice", 1.5)
    except Exception as e:
        logging.warning(f"get_star_price error: {e}")
        return 1.5


def create_stars_order(username: str, count: int, amount: float):
    url = "https://dg-api.wata.pro/api/stars"
    headers = {
        "Authorization": f"Bearer {WATA_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "username": username.strip("@"),
        "count": count,
        "amount": round(amount, 2),
        "description": f"Покупка {count} ⭐ для @{username}",
        "orderId": str(uuid.uuid4()),
        "successRedirectUrl": f"https://t.me/Epic_Stars_Gift_bot",
        "failRedirectUrl": f"https://t.me/Epic_Stars_Gift_bot",
    }
    try:
        r = requests.post(url, json=payload, headers=headers, timeout=30)
        r.raise_for_status()
        return r.json().get("paymentLink")
    except Exception as e:
        logging.error(f"create_stars_order error: {e}")
        return None


def create_premium_payment(username: str, months: int, price: int):
    url = "https://api.wata.pro/api/h2h/links"
    headers = {
        "Authorization": f"Bearer {WATA_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "amount": float(price),
        "currency": "RUB",
        "description": f"Telegram Premium {months} мес. для @{username}",
        "orderId": str(uuid.uuid4()),
        "successRedirectUrl": f"https://t.me/Epic_Stars_Gift_bot",
        "failRedirectUrl": f"https://t.me/Epic_Stars_Gift_bot",
    }
    try:
        r = requests.post(url, json=payload, headers=headers, timeout=30)
        r.raise_for_status()
        data = r.json()
        return data.get("link") or data.get("paymentLink") or data.get("url")
    except Exception as e:
        error_text = r.text if "r" in locals() else "No response"
        logging.error(f"create_premium_payment error: {e} | {error_text}")
        return None


# ================== ВСПОМОГАТЕЛЬНЫЕ ==================

async def send_stars_payment(message: types.Message, username: str, count: int):
    """Получить цену и создать заказ на звёзды, отправить ссылку."""
    username_clean = username.strip("@")

    # Проверяем существование пользователя и получаем цену
    url = f"https://dg-api.wata.pro/api/stars/price?Username={username_clean}"
    headers = {"Authorization": f"Bearer {WATA_TOKEN}"}
    try:
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code == 400:
            err = r.json().get("error", {})
            if err.get("code") == "STR_1002":
                await message.answer(
                    f"❌ Пользователь @{username_clean} не найден в Telegram.\n"
                    "Убедитесь, что юзернейм введён правильно.",
                    reply_markup=back_to_main(),
                )
                return
        r.raise_for_status()
        min_price = r.json().get("minPrice", 1.5)
    except Exception:
        min_price = 1.5

    amount = round(min_price * count, 2)
    payment_link = create_stars_order(username_clean, count, amount)

    if payment_link:
        await message.answer(
            f"✅ <b>Заказ создан!</b>\n\n"
            f"👤 Получатель: @{username_clean}\n"
            f"⭐ Количество: {count}\n"
            f"💰 Сумма: <b>{amount} ₽</b>\n\n"
            f"👇 Нажмите кнопку для оплаты:",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="💳 Оплатить", url=payment_link)],
                [InlineKeyboardButton(text="◀️ Главное меню", callback_data="main_menu")],
            ]),
        )
    else:
        await message.answer(
            "❌ Ошибка создания платежа. Попробуйте позже или напишите в поддержку.",
            reply_markup=back_to_main(),
        )


async def send_premium_payment(message: types.Message, username: str, months: int, price: int, label: str):
    """Создать заказ на Premium и отправить ссылку."""
    username_clean = username.strip("@")
    payment_link = create_premium_payment(username_clean, months, price)

    if payment_link:
        await message.answer(
            f"✅ <b>Заказ на Premium создан!</b>\n\n"
            f"👤 Получатель: @{username_clean}\n"
            f"💎 Срок: {label}\n"
            f"💰 Сумма: <b>{price} ₽</b>\n\n"
            f"⏳ Счёт действителен 90 минут.\n\n"
            f"⚠️ Оплачивая, вы подтверждаете, что покупаете Telegram Premium "
            f"для себя или в подарок, и НЕ оплачиваете услуги третьих лиц.\n\n"
            f"👇 Нажмите кнопку для оплаты:",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="💳 Оплатить", url=payment_link)],
                [InlineKeyboardButton(text="◀️ Главное меню", callback_data="main_menu")],
            ]),
        )
    else:
        await message.answer(
            "❌ Ошибка создания платежа. Попробуйте позже или напишите в поддержку.",
            reply_markup=back_to_main(),
        )


# ================== ХЭНДЛЕРЫ ==================

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "👋 <b>Добро пожаловать в EpicStars!</b>\n\n"
        "Здесь можно приобрести Telegram звезды быстро, безопасно а главное - дешево!\n\n"
        "☺️ Чтобы продолжить, просто нажмите нужную вам кнопку ниже!",
        parse_mode="HTML",
        reply_markup=main_menu(),
    )


@dp.message(Command("cancel"))
async def cmd_cancel(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "❌ Действие отменено.",
        reply_markup=main_menu(),
    )


@dp.callback_query(F.data == "cancel")
async def cb_cancel(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "👋 <b>Добро пожаловать в EpicStars!</b>\n\n"
        "Здесь можно приобрести Telegram звезды быстро, безопасно а главное - дешево!\n\n"
        "☺️ Чтобы продолжить, просто нажмите нужную вам кнопку ниже!",
        parse_mode="HTML",
        reply_markup=main_menu(),
    )


@dp.callback_query(F.data == "main_menu")
async def cb_main_menu(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "👋 <b>Добро пожаловать в EpicStars!</b>\n\n"
        "Здесь можно приобрести Telegram звезды быстро, безопасно а главное - дешево!\n\n"
        "☺️ Чтобы продолжить, просто нажмите нужную вам кнопку ниже!",
        parse_mode="HTML",
        reply_markup=main_menu(),
    )


# ── ЗВЁЗДЫ ──

@dp.callback_query(F.data == "buy_stars")
async def cb_buy_stars(callback: types.CallbackQuery):
    username = callback.from_user.username or f"id{callback.from_user.id}"
    await callback.message.edit_text(
        f"⭐️ <b>Введите нужное количество звезд (50 - 1 000 000)</b>\n\n"
        f"👤 Покупка для: @{username}",
        parse_mode="HTML",
        reply_markup=stars_menu(),
    )


@dp.callback_query(F.data.startswith("stars_preset_"))
async def cb_stars_preset(callback: types.CallbackQuery):
    count = int(callback.data.split("_")[-1])
    username = callback.from_user.username or f"id{callback.from_user.id}"
    await callback.answer()
    await callback.message.edit_text(
        f"⏳ Создаём заказ на {count} ⭐ для @{username}...",
        parse_mode="HTML",
    )
    await send_stars_payment(callback.message, username, count)


@dp.callback_query(F.data == "stars_friend")
async def cb_stars_friend(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(StarsStates.waiting_username)
    await callback.message.edit_text(
        "👤 <b>Введите юзернейм аккаунта, на который будут отправлены звезды.</b>\n\n"
        "Убедитесь, что аккаунт существует.\n\n"
        "Отменить - /cancel",
        parse_mode="HTML",
    )


@dp.message(StarsStates.waiting_username)
async def fsm_stars_username(message: types.Message, state: FSMContext):
    username = message.text.strip().lstrip("@")
    await state.update_data(username=username, mode="stars")
    await state.set_state(StarsStates.waiting_amount)
    await message.answer(
        f"⭐️ Покупка для @{username}\n\n"
        f"Выберите количество звёзд:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="⭐ 50", callback_data="friend_stars_50"),
                InlineKeyboardButton(text="⭐ 100", callback_data="friend_stars_100"),
                InlineKeyboardButton(text="⭐ 500", callback_data="friend_stars_500"),
            ],
            [
                InlineKeyboardButton(text="⭐ 1 000", callback_data="friend_stars_1000"),
                InlineKeyboardButton(text="⭐ 5 000", callback_data="friend_stars_5000"),
            ],
            [InlineKeyboardButton(text="❌ Отменить", callback_data="cancel")],
        ]),
    )


@dp.callback_query(F.data.startswith("friend_stars_"))
async def cb_friend_stars_amount(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    username = data.get("username", "")
    count = int(callback.data.split("_")[-1])
    await state.clear()
    await callback.answer()
    await callback.message.edit_text(f"⏳ Создаём заказ на {count} ⭐ для @{username}...")
    await send_stars_payment(callback.message, username, count)


# ── ПРЕМИУМ ──

@dp.callback_query(F.data == "buy_premium")
async def cb_buy_premium(callback: types.CallbackQuery):
    username = callback.from_user.username or f"id{callback.from_user.id}"
    await callback.message.edit_text(
        f"💎 <b>Premium для @{username}</b>\n\n"
        f"Выберите срок подписки:",
        parse_mode="HTML",
        reply_markup=premium_menu(),
    )


PREMIUM_DATA = {
    "3":  (3,  1120, "3 месяца"),
    "6":  (6,  1490, "6 месяцев"),
    "12": (12, 2700, "1 год"),
}


@dp.callback_query(F.data.startswith("premium_") & ~F.data.endswith("friend"))
async def cb_premium_selected(callback: types.CallbackQuery):
    key = callback.data.split("_")[1]
    if key not in PREMIUM_DATA:
        return
    months, price, label = PREMIUM_DATA[key]
    username = callback.from_user.username or f"id{callback.from_user.id}"
    await callback.answer()
    await callback.message.edit_text(f"⏳ Создаём заказ на Premium ({label}) для @{username}...")
    await send_premium_payment(callback.message, username, months, price, label)


@dp.callback_query(F.data == "premium_friend")
async def cb_premium_friend(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(PremiumStates.waiting_username)
    await callback.message.edit_text(
        "👤 <b>Введите юзернейм аккаунта, на который будет активирован Telegram Premium.</b>\n\n"
        "Убедитесь, что аккаунт существует.\n\n"
        "Отменить - /cancel",
        parse_mode="HTML",
    )


@dp.message(PremiumStates.waiting_username)
async def fsm_premium_username(message: types.Message, state: FSMContext):
    username = message.text.strip().lstrip("@")
    await state.update_data(username=username)
    await state.clear()
    await message.answer(
        f"💎 Покупка Premium для @{username}\n\n"
        f"Выберите срок подписки:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="⭐ 3 Месяца", callback_data=f"friend_premium_{username}_3"),
                InlineKeyboardButton(text="⭐ 6 Месяцев", callback_data=f"friend_premium_{username}_6"),
            ],
            [InlineKeyboardButton(text="⭐ 1 Год", callback_data=f"friend_premium_{username}_12")],
            [InlineKeyboardButton(text="❌ Отменить", callback_data="cancel")],
        ]),
    )


@dp.callback_query(F.data.startswith("friend_premium_"))
async def cb_friend_premium_selected(callback: types.CallbackQuery):
    # формат: friend_premium_{username}_{months}
    parts = callback.data.split("_")
    # parts: ['friend', 'premium', username..., months]
    months_key = parts[-1]
    username = "_".join(parts[2:-1])
    if months_key not in PREMIUM_DATA:
        return
    months, price, label = PREMIUM_DATA[months_key]
    await callback.answer()
    await callback.message.edit_text(f"⏳ Создаём заказ на Premium ({label}) для @{username}...")
    await send_premium_payment(callback.message, username, months, price, label)


# ================== ЗАПУСК ==================

async def main():
    logging.basicConfig(level=logging.INFO)
    print("🤖 Бот EpicStars запущен!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
