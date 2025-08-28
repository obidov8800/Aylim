# bot/main.py

# 1-QADAM: Django proyektining yo'lini ko'rsatish (HAR DOIM BIRINCHI KELADI!)
import os
import sys
import django
import asyncio
import logging

# Python'ga loyiha papkasini tanitish
project_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_path not in sys.path:
    sys.path.append(project_path)

# Django sozlamalarini yuklash
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "aylim_system.settings")
django.setup()

# 2-QADAM: Endi boshqa modullarni import qilish
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from bot.config import BOT_TOKEN
from bot.handlers import start_auth, user_menu, admin_actions

async def main():
    # Logging sozlamalari
    logging.basicConfig(level=logging.INFO)

    # Bot va Dispatcher obyektlari
    bot = Bot(token=BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Routerlarni ulash
    dp.include_router(start_auth.router)
    dp.include_router(user_menu.router)
    dp.include_router(admin_actions.router)

    # Botni ishga tushirish
    print("Bot ishga tushmoqda...")
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Bot to'xtatildi.")