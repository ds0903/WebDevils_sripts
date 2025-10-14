import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from bot.config import BOT_TOKEN
from bot.handlers_aiogram import auth, accounts, keywords, stats, settings, run_bot
from bot.utils import logger, load_authorized_users

async def main():
    load_authorized_users()
    
    bot = Bot(token=BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    dp.include_router(auth.router)
    dp.include_router(accounts.router)
    dp.include_router(keywords.router)
    dp.include_router(stats.router)
    dp.include_router(settings.router)
    dp.include_router(run_bot.router)
    
    bot_info = await bot.get_me()
    print("=" * 60)
    print("  🤖 TELEGRAM BOT ЗАПУЩЕНО!")
    print("=" * 60)
    print(f"  Bot: @{bot_info.username}")
    print(f"  Name: {bot_info.first_name}")
    print("=" * 60)
    logger.info(f"Бот @{bot_info.username} запущено!")
    
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
