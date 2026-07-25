"""Асинхронный слой SQLite с атомарной защитой слотов."""

from pathlib import Path

import aiosqlite

from config import DEFAULT_SERVICE_DURATION_MINUTES
from data.seed import BARBERS, SERVICES

SCHEMA = """
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY, telegram_id INTEGER UNIQUE NOT NULL, username TEXT,
    full_name TEXT NOT NULL, phone TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS services(
    id INTEGER PRIMARY KEY, name TEXT NOT NULL, description TEXT, price REAL NOT NULL,
    duration_minutes INTEGER NOT NULL CHECK(duration_minutes > 0), is_active INTEGER DEFAULT 1
);
CREATE TABLE IF NOT EXISTS barbers(
    id INTEGER PRIMARY KEY, name TEXT NOT NULL, specialization TEXT, experience INTEGER,
    rating REAL, description TEXT, is_active INTEGER DEFAULT 1
);
CREATE TABLE IF NOT EXISTS appointments(
    id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id),
    service_id INTEGER NOT NULL REFERENCES services(id), barber_id INTEGER NOT NULL REFERENCES barbers(id),
    appointment_date TEXT NOT NULL, appointment_time TEXT NOT NULL,
    customer_name TEXT NOT NULL, customer_phone TEXT NOT NULL, total_price REAL NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('confirmed','cancelled','completed')),
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE UNIQUE INDEX IF NOT EXISTS one_active_barber_slot
ON appointments(barber_id, appointment_date, appointment_time) WHERE status='confirmed';
"""


class Database:
    def __init__(self, path: str):
        self.path = path

    async def _connect(self) -> aiosqlite.Connection:
        db = await aiosqlite.connect(self.path)
        db.row_factory = aiosqlite.Row
        await db.execute("PRAGMA foreign_keys=ON")
        await db.execute("PRAGMA busy_timeout=5000")
        return db

    async def init(self) -> None:
        path = Path(self.path)
        if path.parent != Path("."):
            path.parent.mkdir(parents=True, exist_ok=True)
        db = await self._connect()
        try:
            await db.executescript(SCHEMA)
            service_count = (
                await (await db.execute("SELECT COUNT(*) FROM services")).fetchone()
            )[0]
            if not service_count:
                await db.executemany(
                    "INSERT INTO services(name,description,price,duration_minutes) VALUES(?,?,?,?)",
                    [
                        (name, desc, price, DEFAULT_SERVICE_DURATION_MINUTES)
                        for name, desc, price in SERVICES
                    ],
                )
            barber_count = (
                await (await db.execute("SELECT COUNT(*) FROM barbers")).fetchone()
            )[0]
            if not barber_count:
                await db.executemany(
                    "INSERT INTO barbers(name,specialization,experience,rating,description) VALUES(?,?,?,?,?)",
                    BARBERS,
                )
            await db.commit()
        finally:
            await db.close()

    async def all(self, sql: str, args: tuple = ()):
        db = await self._connect()
        try:
            cursor = await db.execute(sql, args)
            return await cursor.fetchall()
        finally:
            await db.close()

    async def one(self, sql: str, args: tuple = ()):
        rows = await self.all(sql, args)
        return rows[0] if rows else None

    async def upsert_user(
        self,
        telegram_id: int,
        username: str | None,
        name: str,
        phone: str | None = None,
    ):
        db = await self._connect()
        try:
            await db.execute(
                """INSERT INTO users(telegram_id,username,full_name,phone) VALUES(?,?,?,?)
                ON CONFLICT(telegram_id) DO UPDATE SET
                username=COALESCE(excluded.username,users.username), full_name=excluded.full_name,
                phone=COALESCE(excluded.phone,users.phone)""",
                (telegram_id, username, name, phone),
            )
            await db.commit()
        finally:
            await db.close()
        return await self.one("SELECT * FROM users WHERE telegram_id=?", (telegram_id,))

    async def create_appointment(
        self, telegram_id, service_id, barber_id, day, time, name, phone
    ):
        user = await self.upsert_user(telegram_id, None, name, phone)
        db = await self._connect()
        try:
            # The unique partial index makes this final check atomic even after two simultaneous clicks.
            cursor = await db.execute(
                """INSERT INTO appointments(
                    user_id,service_id,barber_id,appointment_date,appointment_time,
                    customer_name,customer_phone,total_price,status
                )
                SELECT ?,s.id,b.id,?,?,?,?,s.price,'confirmed'
                FROM services s JOIN barbers b ON b.id=?
                WHERE s.id=? AND s.is_active=1 AND b.is_active=1""",
                (user["id"], day, time, name, phone, barber_id, service_id),
            )
            if cursor.rowcount != 1:
                await db.rollback()
                return None
            await db.commit()
            return cursor.lastrowid
        except aiosqlite.IntegrityError:
            await db.rollback()
            return None
        finally:
            await db.close()

    async def cancel(self, appointment_id: int) -> bool:
        db = await self._connect()
        try:
            cursor = await db.execute(
                "UPDATE appointments SET status='cancelled' WHERE id=? AND status='confirmed'",
                (appointment_id,),
            )
            await db.commit()
            return cursor.rowcount == 1
        finally:
            await db.close()
