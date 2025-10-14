from aiogram import Router, F
from aiogram.types import CallbackQuery

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from database import Database
from bot.utils import is_authorized, logger
from bot.keyboards_aiogram import back_button_markup

router = Router()
db = Database()

@router.callback_query(F.data == "menu_settings")
async def show_settings_menu(callback: CallbackQuery):
    if not is_authorized(callback.from_user.id):
        await callback.answer("❌ Доступ заборонено!", show_alert=True)
        return
    
    settings = {
        'delay_between_comments_min': db.get_setting('delay_between_comments_min'),
        'delay_between_comments_max': db.get_setting('delay_between_comments_max'),
        'delay_between_posts_min': db.get_setting('delay_between_posts_min'),
        'delay_between_posts_max': db.get_setting('delay_between_posts_max'),
        'delay_between_accounts_min': db.get_setting('delay_between_accounts_min'),
        'delay_between_accounts_max': db.get_setting('delay_between_accounts_max'),
        'max_post_age_hours': db.get_setting('max_post_age_hours'),
        'run_interval_minutes': db.get_setting('run_interval_minutes')
    }
    
    text = "═══════════════════════════════════\n"
    text += "  ⚙️ <b>НАЛАШТУВАННЯ</b>\n"
    text += "═══════════════════════════════════\n\n"
    text += "📋 <b>Поточні налаштування:</b>\n\n"
    
    text += "⏱️ <b>Затримки між коментарями:</b>\n"
    text += f"   {settings['delay_between_comments_min']}-{settings['delay_between_comments_max']} сек\n\n"
    
    text += "⏱️ <b>Затримки між постами:</b>\n"
    text += f"   {settings['delay_between_posts_min']}-{settings['delay_between_posts_max']} сек\n\n"
    
    text += "⏱️ <b>Затримки між акаунтами:</b>\n"
    text += f"   {settings['delay_between_accounts_min']}-{settings['delay_between_accounts_max']} сек\n\n"
    
    text += "📅 <b>Макс. вік поста:</b>\n"
    text += f"   {settings['max_post_age_hours']} год\n\n"
    
    text += "🔄 <b>Інтервал запуску:</b>\n"
    text += f"   {settings['run_interval_minutes']} хв\n\n"
    
    text += "<i>Налаштування можна змінити в базі даних</i>"
    
    await callback.message.edit_text(text, reply_markup=back_button_markup(), parse_mode='HTML')
    await callback.answer()
    logger.info("Показано меню налаштувань")
