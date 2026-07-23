import logging
from datetime import date
from aiogram import Router, F, Bot
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton as B
from config import *
from data.seed import REVIEWS
from keyboards.common import menu, back, cancel_flow, rows, links
from services.slots import available_dates, free_slots
from states.booking import Booking

router=Router(); log=logging.getLogger(__name__)
def fmt_appt(a): return f"#{a['id']} — {a['appointment_date']} в {a['appointment_time']}\nУслуга: {a['service_name']} (${a['total_price']:.0f})\nМастер: {a['barber_name']}"
async def home(target):
 text=f"Добро пожаловать в {SHOP_NAME}!\n\n{DEMO_NOTICE}"
 await (target.answer(text,reply_markup=menu()) if isinstance(target,Message) else target.message.edit_text(text,reply_markup=menu()))
@router.message(CommandStart())
async def start(m:Message,state:FSMContext,db): await state.clear(); await db.upsert_user(m.from_user.id,m.from_user.username,m.from_user.full_name); await home(m)
@router.message(Command("help"))
async def help_(m:Message): await m.answer("Выберите действие в /start. /cancel отменяет текущий процесс записи. По вопросам используйте раздел «Связаться».")
@router.message(Command("cancel"))
async def cancel_cmd(m:Message,state:FSMContext): await state.clear(); await m.answer("Текущий процесс отменён.",reply_markup=menu())
@router.callback_query(F.data.in_({"menu","stop"}))
async def menu_cb(c:CallbackQuery,state:FSMContext): await state.clear(); await c.answer(); await home(c)
@router.callback_query(F.data=="info")
async def info(c:CallbackQuery):
 await c.answer(); await c.message.edit_text(f"📍 {ADDRESS}\n🕙 Пн–Пт: 10:00–21:00\n🕚 Сб–Вс: 11:00–20:00\n📞 {PHONE}\nTelegram: {TELEGRAM}\nInstagram: {INSTAGRAM}\n\n{DEMO_NOTICE}",reply_markup=InlineKeyboardMarkup(inline_keyboard=[[B(text="Открыть на карте",url=MAP_URL)],[B(text="← Главное меню",callback_data="menu")]]))
@router.callback_query(F.data=="reviews")
async def reviews(c:CallbackQuery):
 await c.answer(); text="⭐ Демонстрационные отзывы\n\n"+"\n\n".join(f"{n} — {'⭐'*r}\n{t}" for n,r,t in REVIEWS)+"\n\nОтзывы используются для демонстрации кейса."
 await c.message.edit_text(text,reply_markup=back())
@router.callback_query(F.data=="contact")
async def contact(c:CallbackQuery): await c.answer(); await c.message.edit_text(f"Связь с барбершопом\n{DEMO_NOTICE}",reply_markup=links())
@router.callback_query(F.data=="book")
async def book(c:CallbackQuery,state:FSMContext,db):
 await c.answer(); await state.clear(); svcs=await db.all("SELECT * FROM services WHERE is_active=1"); await state.set_state(Booking.service); await c.message.edit_text("Выберите услугу:",reply_markup=rows([(f"{x['name']} — ${x['price']:.0f}",x['id']) for x in svcs],"svc"))
@router.callback_query(Booking.service,F.data.startswith("svc:"))
async def service(c:CallbackQuery,state:FSMContext,db):
 await c.answer(); await state.update_data(service=int(c.data.split(':')[1])); bs=await db.all("SELECT * FROM barbers WHERE is_active=1"); await state.set_state(Booking.barber); await c.message.edit_text("Выберите мастера:",reply_markup=rows([(f"{b['name']} · {b['rating']}⭐",b['id']) for b in bs],"bar"))
@router.callback_query(Booking.barber,F.data.startswith("bar:"))
async def barber(c:CallbackQuery,state:FSMContext):
 await c.answer(); await state.update_data(barber=int(c.data.split(':')[1])); await state.set_state(Booking.date); await c.message.edit_text("Выберите дату (доступны ближайшие 14 дней):",reply_markup=rows([(d.strftime('%d.%m, %a'),d.isoformat()) for d in available_dates()],"date"))
@router.callback_query(Booking.date,F.data.startswith("date:"))
async def choose_date(c:CallbackQuery,state:FSMContext,db):
 raw=c.data.split(':',1)[1]
 if date.fromisoformat(raw) not in available_dates(): await c.answer("Дата уже недоступна",show_alert=True); return
 data=await state.get_data(); slots=await free_slots(db,data['barber'],date.fromisoformat(raw)); await c.answer(); await state.update_data(date=raw); await state.set_state(Booking.time)
 await c.message.edit_text("Выберите свободное время:" if slots else "На эту дату свободного времени нет.",reply_markup=rows([(x,x) for x in slots],"time") if slots else cancel_flow())
@router.callback_query(Booking.time,F.data.startswith("time:"))
async def choose_time(c:CallbackQuery,state:FSMContext): await c.answer(); await state.update_data(time=c.data.split(':',1)[1]); await state.set_state(Booking.name); await c.message.edit_text("Введите ваше имя:",reply_markup=cancel_flow())
@router.message(Booking.name)
async def name(m:Message,state:FSMContext):
 if not m.text or len(m.text.strip())<2: await m.answer("Введите имя текстом (минимум 2 символа)."); return
 await state.update_data(name=m.text.strip()[:100]); await state.set_state(Booking.phone); await m.answer("Введите номер телефона:",reply_markup=cancel_flow())
@router.message(Booking.phone)
async def phone(m:Message,state:FSMContext,db):
 p=(m.text or '').strip()
 if len(p)<7 or not any(x.isdigit() for x in p): await m.answer("Введите корректный номер телефона."); return
 await state.update_data(phone=p[:30]); d=await state.get_data(); s=await db.one("SELECT * FROM services WHERE id=?",(d['service'],)); b=await db.one("SELECT * FROM barbers WHERE id=?",(d['barber'],)); await state.set_state(Booking.confirm)
 await m.answer(f"Проверьте запись:\n{s['name']} — ${s['price']:.0f}\nМастер: {b['name']}\n{d['date']} в {d['time']}\nИмя: {d['name']}\nТелефон: {p}",reply_markup=InlineKeyboardMarkup(inline_keyboard=[[B(text="Подтвердить",callback_data="confirm")],[B(text="Отменить процесс",callback_data="stop")]]))
@router.callback_query(Booking.confirm,F.data=="confirm")
async def confirm(c:CallbackQuery,state:FSMContext,db,bot:Bot,admin_id:int):
 await c.answer(); d=await state.get_data()
 if date.fromisoformat(d['date']) not in available_dates() or d['time'] not in await free_slots(db,d['barber'],date.fromisoformat(d['date'])): await state.clear(); await c.message.edit_text("Это время уже недоступно. Пожалуйста, начните запись заново.",reply_markup=menu()); return
 aid=await db.create_appointment(c.from_user.id,d['service'],d['barber'],d['date'],d['time'],d['name'],d['phone'])
 if not aid: await state.clear(); await c.message.edit_text("Время только что заняли. Выберите другое.",reply_markup=menu()); return
 a=await db.one("SELECT a.*,s.name service_name,b.name barber_name FROM appointments a JOIN services s ON s.id=a.service_id JOIN barbers b ON b.id=a.barber_id WHERE a.id=?",(aid,)); await state.clear(); await c.message.edit_text("✅ Запись подтверждена!\n"+fmt_appt(a),reply_markup=menu())
 try: await bot.send_message(admin_id,"🆕 Новая запись\n"+fmt_appt(a)+f"\nКлиент: {a['customer_name']}\nТелефон: {a['customer_phone']}\nTelegram ID: {c.from_user.id}")
 except Exception: log.exception("Не удалось уведомить администратора")
@router.callback_query(F.data=="mine")
async def mine(c:CallbackQuery,db):
 await c.answer(); a=await db.one("SELECT a.*,s.name service_name,b.name barber_name FROM appointments a JOIN users u ON u.id=a.user_id JOIN services s ON s.id=a.service_id JOIN barbers b ON b.id=a.barber_id WHERE u.telegram_id=? AND a.status='confirmed' AND (a.appointment_date>date('now') OR (a.appointment_date=date('now') AND a.appointment_time>=time('now'))) ORDER BY a.appointment_date,a.appointment_time LIMIT 1",(c.from_user.id,))
 if not a: await c.message.edit_text("У вас нет ближайших активных записей.",reply_markup=InlineKeyboardMarkup(inline_keyboard=[[B(text="Записаться",callback_data="book")],[B(text="Главное меню",callback_data="menu")]])); return
 await c.message.edit_text("Ваша ближайшая запись:\n"+fmt_appt(a),reply_markup=InlineKeyboardMarkup(inline_keyboard=[[B(text="Отменить запись",callback_data=f"askcancel:{a['id']}")],[B(text="Главное меню",callback_data="menu")]]))
@router.callback_query(F.data.startswith("askcancel:"))
async def ask_cancel(c:CallbackQuery):
 aid=c.data.split(':')[1]; await c.answer(); await c.message.edit_text("Точно отменить запись?",reply_markup=InlineKeyboardMarkup(inline_keyboard=[[B(text="Да, отменить",callback_data=f"docancel:{aid}")],[B(text="Нет",callback_data="mine")]]))
@router.callback_query(F.data.startswith("docancel:"))
async def do_cancel(c:CallbackQuery,db,bot:Bot,admin_id:int):
 aid=int(c.data.split(':')[1]); a=await db.one("SELECT a.* FROM appointments a JOIN users u ON u.id=a.user_id WHERE a.id=? AND u.telegram_id=?",(aid,c.from_user.id))
 if not a or not await db.cancel(aid): await c.answer("Запись уже отменена",show_alert=True); return
 await c.answer(); await c.message.edit_text("✅ Запись отменена. Выбранное время снова свободно.",reply_markup=menu())
 try: await bot.send_message(admin_id,f"❌ Клиент отменил запись #{aid}\n{a['appointment_date']} в {a['appointment_time']}\n{a['customer_name']}, {a['customer_phone']}")
 except Exception: log.exception("Не удалось уведомить администратора")
