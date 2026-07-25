import logging
from datetime import date, datetime
from aiogram import Router, F
from aiogram.filters import Command
from aiogram import Bot
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton as B,
)
from keyboards.common import admin

router = Router()
log = logging.getLogger(__name__)


def allowed(uid, admin_id):
    return uid == admin_id


def line(a):
    return f"#{a['id']} {a['appointment_date']} {a['appointment_time']} · {a['customer_name']} · {a['barber']} · {a['service']} · {a['customer_phone']}"


@router.message(Command("admin"))
async def panel(m: Message, admin_id: int):
    if not allowed(m.from_user.id, admin_id):
        await m.answer("Доступ запрещён.")
        return
    await m.answer("Панель администратора", reply_markup=admin())


@router.callback_query(
    F.data.in_({"adm:today", "adm:next", "adm:all", "adm:cancel", "adm:stats"})
)
async def action(c: CallbackQuery, db, admin_id: int):
    if not allowed(c.from_user.id, admin_id):
        await c.answer("Доступ запрещён", show_alert=True)
        return
    act = c.data.split(":")[1]
    if act == "stats":
        s = await db.one(
            "SELECT (SELECT COUNT(*) FROM users) users,(SELECT COUNT(*) FROM appointments WHERE status='confirmed') active,(SELECT COUNT(*) FROM appointments WHERE status='cancelled') cancelled,(SELECT COALESCE(SUM(total_price),0) FROM appointments WHERE status='confirmed') revenue"
        )
        text = f"📊 Статистика\nПользователей: {s['users']}\nАктивных записей: {s['active']}\nОтменённых: {s['cancelled']}\nПотенциальная выручка: ${s['revenue']:.0f}"
        markup = admin()
    elif act == "cancel":
        items = await db.all(
            "SELECT id,appointment_date,appointment_time,customer_name FROM appointments WHERE status='confirmed' ORDER BY appointment_date,appointment_time LIMIT 30"
        )
        text = "Выберите запись для отмены:" if items else "Активных записей нет."
        markup = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    B(
                        text=f"#{a['id']} {a['appointment_date']} {a['appointment_time']} {a['customer_name']}",
                        callback_data=f"admx:{a['id']}",
                    )
                ]
                for a in items
            ]
            + [[B(text="Назад", callback_data="adm:all")]]
        )
    else:
        where = "a.status='confirmed'"
        args = ()
        if act == "today":
            where += " AND a.appointment_date=?"
            args = (date.today().isoformat(),)
        elif act == "next":
            now = datetime.now()
            where += " AND (a.appointment_date>? OR (a.appointment_date=? AND a.appointment_time>=?))"
            args = (
                now.date().isoformat(),
                now.date().isoformat(),
                now.strftime("%H:%M"),
            )
        items = await db.all(
            f"SELECT a.*,s.name service,b.name barber FROM appointments a JOIN services s ON s.id=a.service_id JOIN barbers b ON b.id=a.barber_id WHERE {where} ORDER BY a.appointment_date,a.appointment_time LIMIT 50",
            args,
        )
        text = (
            ("Записи:\n" + "\n".join(line(x) for x in items))
            if items
            else "Записей нет."
        )
        markup = admin()
    await c.answer()
    await c.message.edit_text(text, reply_markup=markup)


@router.callback_query(F.data.regexp(r"^admx:\d+$"))
async def admin_cancel(c: CallbackQuery, db, admin_id: int, bot: Bot):
    if not allowed(c.from_user.id, admin_id):
        await c.answer("Доступ запрещён", show_alert=True)
        return
    appointment_id = int(c.data.split(":")[1])
    appointment = await db.one(
        "SELECT a.*,u.telegram_id FROM appointments a JOIN users u ON u.id=a.user_id WHERE a.id=?",
        (appointment_id,),
    )
    ok = await db.cancel(appointment_id)
    await c.answer("Запись отменена" if ok else "Запись уже неактивна", show_alert=True)
    await c.message.edit_text("Панель администратора", reply_markup=admin())
    if ok and appointment:
        try:
            await bot.send_message(
                appointment["telegram_id"],
                f"❌ Администратор отменил запись #{appointment_id}\n{appointment['appointment_date']} в {appointment['appointment_time']}.",
            )
        except Exception:
            log.exception("Не удалось уведомить клиента об отмене")
