from aiogram import Router, F
from aiogram.types import CallbackQuery
import subprocess
import os

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from database import Database
from bot.utils import is_authorized, logger
from bot.keyboards_aiogram import run_menu_markup, back_button_markup
from bot.config import BASE_DIR

router = Router()
db = Database()

@router.callback_query(F.data == "menu_run")
async def show_run_menu(callback: CallbackQuery):
    if not is_authorized(callback.from_user.id):
        await callback.answer("❌ Доступ заборонено!", show_alert=True)
        return
    
    accounts = [a for a in db.get_all_accounts() if a['enabled']]
    keywords = [k for k in db.get_all_keywords() if k['enabled']]
    
    text = "═══════════════════════════════════\n"
    text += "  🚀 <b>ЗАПУСК БОТА</b>\n"
    text += "═══════════════════════════════════\n\n"
    
    if not accounts:
        text += "❌ Немає активних акаунтів!\n\n"
    else:
        text += f"✅ Активних акаунтів: {len(accounts)}\n"
    
    if not keywords:
        text += "❌ Немає активних ключових слів!\n\n"
    else:
        text += f"✅ Активних ключових слів: {len(keywords)}\n"
        
        follow_keywords = [k for k in keywords if k.get('should_follow', False)]
        if follow_keywords:
            kw_list = ', '.join([f'"{k["keyword"]}"' for k in follow_keywords[:3]])
            if len(follow_keywords) > 3:
                kw_list += f" та ще {len(follow_keywords) - 3}"
            text += f"👤 З підпискою: {len(follow_keywords)}\n   ({kw_list})\n"
    
    if not accounts or not keywords:
        await callback.message.edit_text(text, reply_markup=back_button_markup(), parse_mode='HTML')
        logger.warning("Спроба запуску без акаунтів/ключових слів")
        await callback.answer()
        return
    
    text += "\n<b>Виберіть режим роботи:</b>"
    
    await callback.message.edit_text(text, reply_markup=run_menu_markup(), parse_mode='HTML')
    await callback.answer()

@router.callback_query(F.data == "run_once")
async def run_bot_once(callback: CallbackQuery):
    if not is_authorized(callback.from_user.id):
        await callback.answer("❌ Доступ заборонено!", show_alert=True)
        return
    
    await callback.message.answer(
        "▶️ <b>Запускаю бота один раз...</b>\n\nПроцес виконується в фоні.",
        parse_mode='HTML'
    )
    
    try:
        subprocess.Popen(
            ['python', 'main.py', '--once'],
            cwd=BASE_DIR,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )
        await callback.message.answer(
            "✅ Бот запущено!\n\nПеревірте статистику через деякий час.",
            reply_markup=back_button_markup()
        )
        logger.info("✅ Бот запущено в режимі 'один раз'")
    except Exception as e:
        logger.error(f"Помилка запуску бота: {e}")
        await callback.message.answer(f"❌ Помилка: {e}")
    
    await callback.answer()

@router.callback_query(F.data == "run_loop")
async def run_bot_loop(callback: CallbackQuery):
    if not is_authorized(callback.from_user.id):
        await callback.answer("❌ Доступ заборонено!", show_alert=True)
        return
    
    await callback.message.answer(
        "▶️ <b>Запускаю бота в циклі...</b>\n\n⚠️ Бот буде працювати в фоні до зупинки!",
        parse_mode='HTML'
    )
    
    try:
        subprocess.Popen(
            ['python', 'main.py'],
            cwd=BASE_DIR,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )
        await callback.message.answer(
            "✅ Бот запущено в циклі!\n\n"
            "Для зупинки завершіть процес <code>python main.py</code>",
            parse_mode='HTML',
            reply_markup=back_button_markup()
        )
        logger.info("✅ Бот запущено в циклічному режимі")
    except Exception as e:
        logger.error(f"Помилка запуску бота в циклі: {e}")
        await callback.message.answer(f"❌ Помилка: {e}")
    
    await callback.answer()
