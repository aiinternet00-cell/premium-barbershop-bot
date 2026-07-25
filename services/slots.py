from datetime import date, datetime, timedelta
from config import BOOKING_DAYS, WORK_HOURS, SLOT_INTERVAL_MINUTES


def available_dates(today=None):
    today = today or date.today()
    return [today + timedelta(days=i) for i in range(BOOKING_DAYS)]


def day_slots(day):
    start, end = WORK_HOURS[day.weekday()]
    return [
        f"{minutes // 60:02d}:{minutes % 60:02d}"
        for minutes in range(start * 60, end * 60, SLOT_INTERVAL_MINUTES)
    ]


async def free_slots(db, barber_id, day, now=None):
    now = now or datetime.now()
    busy = {
        row["appointment_time"]
        for row in await db.all(
            """SELECT appointment_time FROM appointments
            WHERE barber_id=? AND appointment_date=? AND status='confirmed'""",
            (barber_id, day.isoformat()),
        )
    }
    return [
        slot
        for slot in day_slots(day)
        if slot not in busy
        and (
            day > now.date()
            or datetime.combine(day, datetime.strptime(slot, "%H:%M").time()) > now
        )
    ]
