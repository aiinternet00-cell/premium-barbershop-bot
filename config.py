"""Настройки приложения: все демонстрационные данные меняются здесь."""

from dataclasses import dataclass
import os
from pathlib import Path


def _load_dotenv():
    """Минимальный загрузчик .env без побочных зависимостей."""
    path = Path(".env")
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


_load_dotenv()

SHOP_NAME = "Kingsway Barbers"
ADDRESS = "125 Kingsway Street, Downtown"
PHONE = "+1 555 010 2026"
TELEGRAM = "https://t.me/kingsway_demo_admin"
INSTAGRAM = "https://instagram.com/kingsway_demo"
MAP_URL = "https://maps.google.com/?q=125+Kingsway+Street+Downtown"
BOOKING_DAYS = 14
SLOT_INTERVAL_MINUTES = 60
DEFAULT_SERVICE_DURATION_MINUTES = 60
WORK_HOURS = {
    0: (10, 21),
    1: (10, 21),
    2: (10, 21),
    3: (10, 21),
    4: (10, 21),
    5: (11, 20),
    6: (11, 20),
}
DEMO_NOTICE = "⚠️ Все адреса, контакты, цены и отзывы — демонстрационные."


@dataclass(frozen=True)
class Settings:
    bot_token: str
    admin_id: int
    database_path: str


def load_settings() -> Settings:
    token = os.getenv("BOT_TOKEN", "").strip()
    admin = os.getenv("ADMIN_ID", "").strip()
    if not token or not admin:
        raise RuntimeError(
            "Обязательные переменные BOT_TOKEN и ADMIN_ID не заданы. См. .env.example"
        )
    try:
        admin_id = int(admin)
    except ValueError as exc:
        raise RuntimeError("ADMIN_ID должен быть целым числом") from exc
    if admin_id <= 0:
        raise RuntimeError("ADMIN_ID должен быть положительным целым числом")
    database_path = os.getenv("DATABASE_PATH", "barbershop.db").strip()
    if not database_path:
        raise RuntimeError("DATABASE_PATH не может быть пустым")
    return Settings(token, admin_id, database_path)
