from aiogram.types import InlineKeyboardButton as B, InlineKeyboardMarkup as M
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import INSTAGRAM, PHONE, TELEGRAM


def menu():
    return M(
        inline_keyboard=[
            [
                B(text="✂️ Записаться", callback_data="book"),
                B(text="📅 Моя запись", callback_data="mine"),
            ],
            [
                B(text="📍 Адрес и режим", callback_data="info"),
                B(text="⭐ Отзывы", callback_data="reviews"),
            ],
            [B(text="☎️ Связаться", callback_data="contact")],
        ]
    )


def back():
    return M(inline_keyboard=[[B(text="← Главное меню", callback_data="menu")]])


def cancel_flow():
    return M(
        inline_keyboard=[
            [
                B(text="Отменить процесс", callback_data="stop"),
                B(text="Главное меню", callback_data="menu"),
            ]
        ]
    )


def rows(items, prefix):
    kb = InlineKeyboardBuilder()
    for label, value in items:
        kb.button(text=label, callback_data=f"{prefix}:{value}")
    kb.adjust(2)
    kb.row(B(text="Отменить процесс", callback_data="stop"))
    return kb.as_markup()


def links():
    phone_url = "tel:" + "".join(ch for ch in PHONE if ch.isdigit() or ch == "+")
    return M(
        inline_keyboard=[
            [B(text="📞 Позвонить", url=phone_url)],
            [
                B(
                    text="💬 Написать администратору",
                    url=TELEGRAM,
                )
            ],
            [B(text="Instagram", url=INSTAGRAM)],
            [B(text="← Главное меню", callback_data="menu")],
        ]
    )


def admin():
    return M(
        inline_keyboard=[
            [B(text="Записи на сегодня", callback_data="adm:today")],
            [
                B(text="Ближайшие записи", callback_data="adm:next"),
                B(text="Все активные записи", callback_data="adm:all"),
            ],
            [
                B(text="Отменить запись", callback_data="adm:cancel"),
                B(text="Статистика", callback_data="adm:stats"),
            ],
            [B(text="Главное меню", callback_data="menu")],
        ]
    )
