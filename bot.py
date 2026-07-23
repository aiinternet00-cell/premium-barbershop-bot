import asyncio, logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import load_settings
from database import Database
from handlers import user, admin

async def main():
 settings=load_settings(); logging.basicConfig(level=logging.INFO,format="%(asctime)s %(levelname)s %(name)s: %(message)s")
 db=Database(settings.database_path); await db.init()
 bot=Bot(settings.bot_token); dp=Dispatcher(storage=MemoryStorage())
 dp["db"]=db; dp["admin_id"]=settings.admin_id
 dp.include_router(admin.router); dp.include_router(user.router)
 try: await dp.start_polling(bot,allowed_updates=dp.resolve_used_update_types())
 finally: await bot.session.close()
if __name__=="__main__": asyncio.run(main())
