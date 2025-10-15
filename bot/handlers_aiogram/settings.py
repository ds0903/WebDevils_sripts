from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from database import Database
from bot.utils import is_authorized, logger
from bot.keyboards_aiogram import cancel_markup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

router = Router()
db = Database()

class SettingsStates(StatesGroup):
    edit_value = State()

def settings_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏱️ Затримки між коментарями", callback_data="setting_comments_delay")],
        [InlineKeyboardButton(text="⏱️ Затримки між постами", callback_data="setting_posts_delay")],
        [InlineKeyboardButton(text="⏱️ Затримки між акаунтами", callback_data="setting_accounts_delay")],
        [InlineKeyboardButton(text="📅 Макс. вік поста", callback_data="setting_max_age")],
        [InlineKeyboardButton(text="🔄 Інтервал запуску", callback_data="setting_run_interval")],
        [InlineKeyboardButton(text="🔇 Headless режим", callback_data="setting_headless")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_main")]
    ])

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
        'run_interval_minutes': db.get_setting('run_interval_minutes'),
        'global_headless_mode': db.get_setting('global_headless_mode') or 'false'
    }
    
    headless_status = "✅ Увімкнено" if settings['global_headless_mode'] == 'true' else "❌ Вимкнено"
    
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
    
    text += "🔇 <b>Глобальний Headless режим:</b>\n"
    text += f"   {headless_status}\n\n"
    
    text += "<i>Натисніть на налаштування щоб змінити</i>"
    
    await callback.message.edit_text(text, reply_markup=settings_keyboard(), parse_mode='HTML')
    await callback.answer()
    logger.info("Показано меню налаштувань")

# ============= РЕДАГУВАННЯ ЗАТРИМОК МІЖ КОМЕНТАРЯМИ =============

@router.callback_query(F.data == "setting_comments_delay")
async def edit_comments_delay(callback: CallbackQuery, state: FSMContext):
    if not is_authorized(callback.from_user.id):
        await callback.answer("❌ Доступ заборонено!", show_alert=True)
        return
    
    current_min = db.get_setting('delay_between_comments_min')
    current_max = db.get_setting('delay_between_comments_max')
    
    await callback.message.answer(
        f"⏱️ <b>Затримки між коментарями</b>\n\n"
        f"Поточні значення: {current_min}-{current_max} сек\n\n"
        f"Введіть нові значення через пробіл (мін макс):\n"
        f"Наприклад: 10 30",
        parse_mode='HTML',
        reply_markup=cancel_markup()
    )
    await state.update_data(setting_type='comments_delay')
    await state.set_state(SettingsStates.edit_value)
    await callback.answer()

# ============= РЕДАГУВАННЯ ЗАТРИМОК МІЖ ПОСТАМИ =============

@router.callback_query(F.data == "setting_posts_delay")
async def edit_posts_delay(callback: CallbackQuery, state: FSMContext):
    if not is_authorized(callback.from_user.id):
        await callback.answer("❌ Доступ заборонено!", show_alert=True)
        return
    
    current_min = db.get_setting('delay_between_posts_min')
    current_max = db.get_setting('delay_between_posts_max')
    
    await callback.message.answer(
        f"⏱️ <b>Затримки між постами</b>\n\n"
        f"Поточні значення: {current_min}-{current_max} сек\n\n"
        f"Введіть нові значення через пробіл (мін макс):\n"
        f"Наприклад: 5 15",
        parse_mode='HTML',
        reply_markup=cancel_markup()
    )
    await state.update_data(setting_type='posts_delay')
    await state.set_state(SettingsStates.edit_value)
    await callback.answer()

# ============= РЕДАГУВАННЯ ЗАТРИМОК МІЖ АКАУНТАМИ =============

@router.callback_query(F.data == "setting_accounts_delay")
async def edit_accounts_delay(callback: CallbackQuery, state: FSMContext):
    if not is_authorized(callback.from_user.id):
        await callback.answer("❌ Доступ заборонено!", show_alert=True)
        return
    
    current_min = db.get_setting('delay_between_accounts_min')
    current_max = db.get_setting('delay_between_accounts_max')
    
    await callback.message.answer(
        f"⏱️ <b>Затримки між акаунтами</b>\n\n"
        f"Поточні значення: {current_min}-{current_max} сек\n\n"
        f"Введіть нові значення через пробіл (мін макс):\n"
        f"Наприклад: 60 120",
        parse_mode='HTML',
        reply_markup=cancel_markup()
    )
    await state.update_data(setting_type='accounts_delay')
    await state.set_state(SettingsStates.edit_value)
    await callback.answer()

# ============= РЕДАГУВАННЯ МАКС. ВІКУ ПОСТА =============

@router.callback_query(F.data == "setting_max_age")
async def edit_max_age(callback: CallbackQuery, state: FSMContext):
    if not is_authorized(callback.from_user.id):
        await callback.answer("❌ Доступ заборонено!", show_alert=True)
        return
    
    current_value = db.get_setting('max_post_age_hours')
    
    await callback.message.answer(
        f"📅 <b>Макс. вік поста</b>\n\n"
        f"Поточне значення: {current_value} год\n\n"
        f"Введіть нове значення (0 = без обмежень):",
        parse_mode='HTML',
        reply_markup=cancel_markup()
    )
    await state.update_data(setting_type='max_age')
    await state.set_state(SettingsStates.edit_value)
    await callback.answer()

# ============= РЕДАГУВАННЯ ІНТЕРВАЛУ ЗАПУСКУ =============

@router.callback_query(F.data == "setting_run_interval")
async def edit_run_interval(callback: CallbackQuery, state: FSMContext):
    if not is_authorized(callback.from_user.id):
        await callback.answer("❌ Доступ заборонено!", show_alert=True)
        return
    
    current_value = db.get_setting('run_interval_minutes')
    
    await callback.message.answer(
        f"🔄 <b>Інтервал запуску</b>\n\n"
        f"Поточне значення: {current_value} хв\n\n"
        f"Введіть нове значення в хвилинах:",
        parse_mode='HTML',
        reply_markup=cancel_markup()
    )
    await state.update_data(setting_type='run_interval')
    await state.set_state(SettingsStates.edit_value)
    await callback.answer()

# ============= HEADLESS РЕЖИМ =============

@router.callback_query(F.data == "setting_headless")
async def toggle_headless(callback: CallbackQuery):
    if not is_authorized(callback.from_user.id):
        await callback.answer("❌ Доступ заборонено!", show_alert=True)
        return
    
    current_value = db.get_setting('global_headless_mode') or 'false'
    new_value = 'false' if current_value == 'true' else 'true'
    
    db.update_setting('global_headless_mode', new_value)
    
    status = "✅ Увімкнено" if new_value == 'true' else "❌ Вимкнено"
    await callback.answer(f"Headless режим: {status}", show_alert=True)
    
    logger.info(f"Змінено глобальний headless режим на {new_value}")
    
    # Оновлюємо меню
    await show_settings_menu(callback)

# ============= ОБРОБКА ВВЕДЕНИХ ЗНАЧЕНЬ =============

@router.message(SettingsStates.edit_value)
async def process_setting_value(message: Message, state: FSMContext):
    if message.text == "❌ Скасувати":
        await state.clear()
        await message.answer("❌ Скасовано", reply_markup=ReplyKeyboardRemove())
        return
    
    data = await state.get_data()
    setting_type = data['setting_type']
    
    try:
        if setting_type in ['comments_delay', 'posts_delay', 'accounts_delay']:
            # Парсимо два значення
            values = message.text.strip().split()
            if len(values) != 2:
                await message.answer("❌ Введіть два значення через пробіл (мін макс)")
                return
            
            min_val = int(values[0])
            max_val = int(values[1])
            
            if min_val >= max_val:
                await message.answer("❌ Мінімум має бути менше максимуму")
                return
            
            # Визначаємо ключі налаштувань
            if setting_type == 'comments_delay':
                db.update_setting('delay_between_comments_min', str(min_val))
                db.update_setting('delay_between_comments_max', str(max_val))
                await message.answer(f"✅ Затримки між коментарями: {min_val}-{max_val} сек", reply_markup=ReplyKeyboardRemove())
            elif setting_type == 'posts_delay':
                db.update_setting('delay_between_posts_min', str(min_val))
                db.update_setting('delay_between_posts_max', str(max_val))
                await message.answer(f"✅ Затримки між постами: {min_val}-{max_val} сек", reply_markup=ReplyKeyboardRemove())
            elif setting_type == 'accounts_delay':
                db.update_setting('delay_between_accounts_min', str(min_val))
                db.update_setting('delay_between_accounts_max', str(max_val))
                await message.answer(f"✅ Затримки між акаунтами: {min_val}-{max_val} сек", reply_markup=ReplyKeyboardRemove())
            
        elif setting_type == 'max_age':
            value = int(message.text.strip())
            if value < 0:
                await message.answer("❌ Значення має бути >= 0")
                return
            
            db.update_setting('max_post_age_hours', str(value))
            await message.answer(f"✅ Макс. вік поста: {value} год", reply_markup=ReplyKeyboardRemove())
            
        elif setting_type == 'run_interval':
            value = int(message.text.strip())
            if value <= 0:
                await message.answer("❌ Значення має бути > 0")
                return
            
            db.update_setting('run_interval_minutes', str(value))
            await message.answer(f"✅ Інтервал запуску: {value} хв", reply_markup=ReplyKeyboardRemove())
        
        logger.info(f"Оновлено налаштування {setting_type}")
        
    except ValueError:
        await message.answer("❌ Введіть коректні числові значення")
        return
    except Exception as e:
        await message.answer(f"❌ Помилка: {e}", reply_markup=ReplyKeyboardRemove())
        logger.error(f"Помилка оновлення налаштувань: {e}")
    
    await state.clear()
