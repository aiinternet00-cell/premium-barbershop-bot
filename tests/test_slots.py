from datetime import date
from services.slots import available_dates, day_slots

def test_fourteen_dates_from_today():
 days=available_dates(date(2026,7,23)); assert len(days)==14; assert days[0]==date(2026,7,23); assert days[-1]==date(2026,8,5)
def test_weekday_and_weekend_hours():
 assert day_slots(date(2026,7,20))[0]=='10:00'; assert day_slots(date(2026,7,20))[-1]=='20:00'
 assert day_slots(date(2026,7,25))[0]=='11:00'; assert day_slots(date(2026,7,25))[-1]=='19:00'
