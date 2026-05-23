from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def get_main_menu() -> ReplyKeyboardMarkup:
    kb = [
        [KeyboardButton(text="⭐ Купить Звезды")],
        [KeyboardButton(text="✨ Telegram Premium"), KeyboardButton(text="💎 Купить TON")],
        [KeyboardButton(text="⭐ Наши отзывы")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


def get_quick_packages_keyboard() -> InlineKeyboardMarkup:
    kb = [
        [InlineKeyboardButton(text="50 ⭐ — 70 ₽", callback_data="package_50")],
        [InlineKeyboardButton(text="100 ⭐ — 140 ₽", callback_data="package_100")],
        [InlineKeyboardButton(text="150 ⭐ — 210 ₽", callback_data="package_150")],
        [InlineKeyboardButton(text="500 ⭐ — 700 ₽", callback_data="package_500")],
        [InlineKeyboardButton(text="1000 ⭐ — 1400 ₽", callback_data="package_1000")],
        [InlineKeyboardButton(text="5000 ⭐ — 7000 ₽", callback_data="package_5000")],
        [InlineKeyboardButton(text="🔢 Своё количество", callback_data="custom_amount")],
        [InlineKeyboardButton(text="👤 Купить Другу", callback_data="buy_for_friend")],
        [InlineKeyboardButton(text="◀️ В главное меню", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)


# НОВАЯ КЛАВИАТУРА — ВЫБОР СПОСОБА ОПЛАТЫ
def get_payment_methods_keyboard(stars: int) -> InlineKeyboardMarkup:
    kb = [
        [InlineKeyboardButton(text="💳 РФ Карты (Wata)", callback_data=f"pay_wata_{stars}")],
        [InlineKeyboardButton(text="🔵 RUB (СБП)", callback_data="pay_sbp")],
        [InlineKeyboardButton(text="◀️ Назад к пакетам", callback_data="back_to_packages")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)