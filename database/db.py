"""Асинхронный слой SQLite с атомарной защитой слотов."""
import aiosqlite
from data.seed import SERVICES, BARBERS
from config import DEFAULT_SERVICE_DURATION_MINUTES

SCHEMA = """
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, telegram_id INTEGER UNIQUE NOT NULL, username TEXT, full_name TEXT NOT NULL, phone TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS services(id INTEGER PRIMARY KEY, name TEXT NOT NULL, description TEXT, price REAL NOT NULL, duration_minutes INTEGER NOT NULL, is_active INTEGER DEFAULT 1);
CREATE TABLE IF NOT EXISTS barbers(id INTEGER PRIMARY KEY, name TEXT NOT NULL, specialization TEXT, experience INTEGER, rating REAL, description TEXT, is_active INTEGER DEFAULT 1);
CREATE TABLE IF NOT EXISTS appointments(id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id), service_id INTEGER NOT NULL REFERENCES services(id), barber_id INTEGER NOT NULL REFERENCES barbers(id), appointment_date TEXT NOT NULL, appointment_time TEXT NOT NULL, customer_name TEXT NOT NULL, customer_phone TEXT NOT NULL, total_price REAL NOT NULL, status TEXT NOT NULL CHECK(status IN ('confirmed','cancelled','completed')), created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE UNIQUE INDEX IF NOT EXISTS one_active_barber_slot ON appointments(barber_id, appointment_date, appointment_time) WHERE status='confirmed';
"""

class Database:
 def __init__(self, path): self.path=path
 async def init(self):
  async with aiosqlite.connect(self.path) as db:
   await db.executescript(SCHEMA)
   if not (await (await db.execute("SELECT COUNT(*) FROM services")).fetchone())[0]:
    await db.executemany("INSERT INTO services(name,description,price,duration_minutes) VALUES(?,?,?,?)", [(n,d,p,DEFAULT_SERVICE_DURATION_MINUTES) for n,d,p in SERVICES])
   if not (await (await db.execute("SELECT COUNT(*) FROM barbers")).fetchone())[0]:
    await db.executemany("INSERT INTO barbers(name,specialization,experience,rating,description) VALUES(?,?,?,?,?)", BARBERS)
   await db.commit()
 async def all(self, sql, args=()):
  async with aiosqlite.connect(self.path) as db:
   db.row_factory=aiosqlite.Row
   return await (await db.execute(sql,args)).fetchall()
 async def one(self, sql, args=()):
  rows=await self.all(sql,args); return rows[0] if rows else None
 async def upsert_user(self, tg, username, name, phone=None):
  async with aiosqlite.connect(self.path) as db:
   await db.execute("INSERT INTO users(telegram_id,username,full_name,phone) VALUES(?,?,?,?) ON CONFLICT(telegram_id) DO UPDATE SET username=excluded.username,full_name=excluded.full_name,phone=COALESCE(excluded.phone,users.phone)",(tg,username,name,phone)); await db.commit()
  return await self.one("SELECT * FROM users WHERE telegram_id=?",(tg,))
 async def create_appointment(self, tg, service, barber, date, time, name, phone):
  user=await self.upsert_user(tg,None,name,phone); svc=await self.one("SELECT * FROM services WHERE id=? AND is_active=1",(service,))
  if not svc: return None
  try:
   async with aiosqlite.connect(self.path) as db:
    cur=await db.execute("INSERT INTO appointments(user_id,service_id,barber_id,appointment_date,appointment_time,customer_name,customer_phone,total_price,status) VALUES(?,?,?,?,?,?,?,?, 'confirmed')",(user['id'],service,barber,date,time,name,phone,svc['price'])); await db.commit(); return cur.lastrowid
  except aiosqlite.IntegrityError: return None
 async def cancel(self, appointment_id):
  async with aiosqlite.connect(self.path) as db:
   cur=await db.execute("UPDATE appointments SET status='cancelled' WHERE id=? AND status='confirmed'",(appointment_id,)); await db.commit(); return cur.rowcount == 1
