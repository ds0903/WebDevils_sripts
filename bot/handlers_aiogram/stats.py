from aiogram import Router, F
from aiogram.types import CallbackQuery
from datetime import datetime

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from database import Database
from bot.utils import is_authorized, logger
from bot.keyboards_aiogram import stats_menu_markup, back_button_markup

router = Router()
db = Database()

@router.callback_query(F.data == "menu_stats")
async def show_stats_menu(callback: CallbackQuery):
    if not is_authorized(callback.from_user.id):
        await callback.answer("❌ Доступ заборонено!", show_alert=True)
        return
    
    stats = db.get_statistics()
    
    text = "═══════════════════════════════════\n"
    text += "  📊 <b>СТАТИСТИКА ТА ІСТОРІЯ</b>\n"
    text += "═══════════════════════════════════\n\n"
    text += "📈 <b>Загальна статистика:</b>\n\n"
    text += f"Всього коментарів: {stats['total']}\n"
    text += f"✅ Успішних: {stats['success']}\n"
    text += f"⚠️ Невдалих: {stats['failed']}\n"
    text += f"❌ Помилок: {stats['error']}\n"
    
    if stats['total'] > 0:
        success_rate = (stats['success'] / stats['total']) * 100
        text += f"\n📊 Success Rate: {success_rate:.1f}%\n"
    
    text += "\n<b>Переглянути історію:</b>"
    
    await callback.message.edit_text(text, reply_markup=stats_menu_markup(), parse_mode='HTML')
    await callback.answer()

@router.callback_query(F.data.in_(["stats_20", "stats_50"]))
async def view_history(callback: CallbackQuery):
    if not is_authorized(callback.from_user.id):
        await callback.answer("❌ Доступ заборонено!", show_alert=True)
        return
    
    limit = 20 if callback.data == "stats_20" else 50
    history = db.get_comment_history(limit)
    
    if not history:
        await callback.answer("⚠️ Історії ще немає", show_alert=True)
        return
    
    text = f"📜 <b>ІСТОРІЯ КОМЕНТАРІВ (останні {limit})</b>\n\n"
    
    for item in history[:15]:
        status_icon = {
            'success': '✅',
            'failed': '⚠️',
            'error': '❌'
        }.get(item['status'], '❓')
        
        # Виправлення: created_at вже datetime об'єкт, не потрібно fromisoformat
        created_at = item['created_at']
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        date = created_at.strftime('%d.%m %H:%M')
        
        text += f"{status_icon} {date} | @{item['username']}\n"
        text += f"   🔑 \"{item['keyword']}\"\n"
        if item['comment_text']:
            preview = item['comment_text'][:35] + "..." if len(item['comment_text']) > 35 else item['comment_text']
            text += f"   💬 {preview}\n"
        text += "\n"
    
    if len(history) > 15:
        text += f"...та ще {len(history) - 15} записів"
    
    await callback.message.answer(text, reply_markup=back_button_markup(), parse_mode='HTML')
    await callback.answer()
    logger.info(f"Показано історію (останні {limit})")
