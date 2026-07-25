from datetime import date, datetime
from services.slots import available_dates, day_slots
from services.slots import free_slots
import asyncio


def test_fourteen_dates_from_today():
    days = available_dates(date(2026, 7, 23))
    assert len(days) == 14
    assert days[0] == date(2026, 7, 23)
    assert days[-1] == date(2026, 8, 5)


def test_weekday_and_weekend_hours():
    assert day_slots(date(2026, 7, 20))[0] == "10:00"
    assert day_slots(date(2026, 7, 20))[-1] == "20:00"
    assert day_slots(date(2026, 7, 25))[0] == "11:00"
    assert day_slots(date(2026, 7, 25))[-1] == "19:00"


def test_past_times_are_not_available():
    class EmptyDatabase:
        async def all(self, _sql, _args):
            return []

    slots = asyncio.run(
        free_slots(EmptyDatabase(), 1, date(2026, 7, 20), datetime(2026, 7, 20, 15, 30))
    )
    assert slots[0] == "16:00"
