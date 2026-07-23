from aiogram.types import InlineKeyboardButton as B, InlineKeyboardMarkup as M
from aiogram.utils.keyboard import InlineKeyboardBuilder

def menu(): return M(inline_keyboard=[[B(text="✂️ Записаться",callback_data="book"),B(text="📅 Моя запись",callback_data="mine")],[B(text="📍 Адрес и режим",callback_data="info"),B(text="⭐ Отзывы",callback_data="reviews")],[B(text="☎️ Связаться",callback_data="contact")]])
def back(): return M(inline_keyboard=[[B(text="← Главное меню",callback_data="menu")]])
def cancel_flow(): return M(inline_keyboard=[[B(text="Отменить процесс",callback_data="stop"),B(text="Главное меню",callback_data="menu")]])
def rows(items, prefix):
 kb=InlineKeyboardBuilder()
 for label,value in items: kb.button(text=label,callback_data=f"{prefix}:{value}")
 kb.adjust(2); kb.row(B(text="Отменить процесс",callback_data="stop")); return kb.as_markup()
def links(): return M(inline_keyboard=[[B(text="📞 Позвонить",url="tel:+15550102026")],[B(text="💬 Написать администратору",url="https://t.me/kingsway_demo_admin")],[B(text="Instagram",url="https://instagram.com/kingsway_demo")],[B(text="← Главное меню",callback_data="menu")]])
def admin(): return M(inline_keyboard=[[B(text="Записи на сегодня",callback_data="adm:today")],[B(text="Ближайшие записи",callback_data="adm:next"),B(text="Все активные записи",callback_data="adm:all")],[B(text="Отменить запись",callback_data="adm:cancel"),B(text="Статистика",callback_data="adm:stats")],[B(text="Главное меню",callback_data="menu")]])
