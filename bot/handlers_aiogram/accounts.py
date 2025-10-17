from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from database import Database
from bot.utils import is_authorized, logger
from bot.keyboards_aiogram import accounts_menu_markup, cancel_markup, yes_no_markup, confirm_delete_markup

router = Router()
db = Database()

class AccountStates(StatesGroup):
    add_username = State()
    add_password = State()
    add_max_comments = State()
    
    edit_select = State()
    edit_menu = State()
    edit_password = State()
    edit_max_comments = State()
    
    toggle_select = State()
    delete_select = State()
    delete_confirm = State()

@router.callback_query(F.data == "menu_accounts")
async def show_accounts_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    if not is_authorized(callback.from_user.id):
        await callback.answer("❌ Доступ заборонено!", show_alert=True)
        return
    
    accounts = db.get_all_accounts()
    
    text = "═══════════════════════════════════\n"
    text += "  👥 <b>УПРАВЛІННЯ АКАУНТАМИ</b>\n"
    text += "═══════════════════════════════════\n\n"
    
    if accounts:
        text += "📋 <b>Список акаунтів:</b>\n\n"
        for acc in accounts:
            status = "🟢" if acc['enabled'] else "🔴"
            text += f"{acc['id']}. {status} @{acc['username']}\n"
            text += f"   Макс: {acc['max_comments_per_run']} коментарів\n\n"
    else:
        text += "⚠️ Акаунтів ще немає\n\n"
    
    text += "<b>Виберіть дію:</b>"
    
    await callback.message.edit_text(text, reply_markup=accounts_menu_markup(), parse_mode='HTML')
    await callback.answer()

@router.callback_query(F.data == "acc_add")
async def add_account_start(callback: CallbackQuery, state: FSMContext):
    if not is_authorized(callback.from_user.id):
        await callback.answer("❌ Доступ заборонено!", show_alert=True)
        return
    
    await callback.message.edit_text(
        "➕ <b>ДОДАВАННЯ АКАУНТУ</b>\n\nВведіть username (Instagram/Threads):",
        parse_mode='HTML',
        reply_markup=cancel_markup("menu_accounts")
    )
    await state.update_data(last_bot_message_id=callback.message.message_id)
    await state.set_state(AccountStates.add_username)
    await callback.answer()

@router.message(AccountStates.add_username)
async def process_add_username(message: Message, state: FSMContext):
    await state.update_data(username=message.text)
    try:
        await message.delete()
    except:
        pass
    
    data = await state.get_data()
    try:
        await message.bot.delete_message(message.chat.id, data.get('last_bot_message_id'))
    except:
        pass
    
    msg = await message.answer(
        f"➕ <b>ДОДАВАННЯ АКАУНТУ</b>\n\nUsername: @{data['username']}\n\nВведіть пароль:",
        parse_mode='HTML',
        reply_markup=cancel_markup("menu_accounts")
    )
    await state.update_data(last_bot_message_id=msg.message_id)
    await state.set_state(AccountStates.add_password)

@router.message(AccountStates.add_password)
async def process_add_password(message: Message, state: FSMContext):
    await state.update_data(password=message.text)
    try:
        await message.delete()
    except:
        pass
    
    data = await state.get_data()
    try:
        await message.bot.delete_message(message.chat.id, data.get('last_bot_message_id'))
    except:
        pass
    
    msg = await message.answer(
        f"➕ <b>ДОДАВАННЯ АКАУНТУ</b>\n\nUsername: @{data['username']}\n\nМаксимум коментарів за запуск? (За замовчуванням 5):",
        parse_mode='HTML',
        reply_markup=cancel_markup("menu_accounts")
    )
    await state.update_data(last_bot_message_id=msg.message_id)
    await state.set_state(AccountStates.add_max_comments)

@router.message(AccountStates.add_max_comments)
async def process_add_max_comments(message: Message, state: FSMContext):
    max_comments = int(message.text) if message.text.isdigit() else 5
    data = await state.get_data()
    
    try:
        await message.delete()
    except:
        pass
    
    try:
        await message.bot.delete_message(message.chat.id, data.get('last_bot_message_id'))
    except:
        pass
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад до головного меню", callback_data="menu_accounts")]
    ])
    
    try:
        account_id = db.create_account(
            data['username'],
            data['password'],
            max_comments,
            True
        )
        
        await message.answer(
            f"✅ <b>Акаунт створено!</b>\n\nID: {account_id}\nUsername: @{data['username']}\nМакс. коментарів: {max_comments}",
            parse_mode='HTML',
            reply_markup=keyboard
        )
        logger.info(f"Створено акаунт @{data['username']} (ID: {account_id})")
    except Exception as e:
        await message.answer(f"❌ <b>Помилка:</b> {e}", parse_mode='HTML', reply_markup=keyboard)
        logger.error(f"Помилка створення акаунту: {e}")
    
    await state.clear()

# ============= РЕДАГУВАННЯ АКАУНТУ =============

@router.callback_query(F.data == "acc_edit")
async def edit_account_start(callback: CallbackQuery, state: FSMContext):
    if not is_authorized(callback.from_user.id):
        await callback.answer("❌ Доступ заборонено!", show_alert=True)
        return
    
    accounts = db.get_all_accounts()
    if not accounts:
        await callback.answer("⚠️ Немає акаунтів", show_alert=True)
        return
    
    text = "✏️ <b>РЕДАГУВАННЯ АКАУНТУ</b>\n\nВведіть ID акаунту:\n\n"
    for acc in accounts:
        status = "🟢" if acc['enabled'] else "🔴"
        text += f"{acc['id']}. {status} @{acc['username']}\n"
    
    await callback.message.edit_text(text, parse_mode='HTML', reply_markup=cancel_markup("menu_accounts"))
    await state.update_data(last_bot_message_id=callback.message.message_id)
    await state.set_state(AccountStates.edit_select)
    await callback.answer()

@router.message(AccountStates.edit_select)
async def process_edit_select(message: Message, state: FSMContext):
    if not message.text.isdigit():
        try:
            await message.delete()
        except:
            pass
        return
    
    account = db.get_account(int(message.text))
    if not account:
        try:
            await message.delete()
        except:
            pass
        data = await state.get_data()
        try:
            await message.bot.delete_message(message.chat.id, data.get('last_bot_message_id'))
        except:
            pass
        
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад до головного меню", callback_data="menu_accounts")]
        ])
        await message.answer("❌ <b>Акаунт не знайдено!</b>", parse_mode='HTML', reply_markup=keyboard)
        await state.clear()
        return
    
    await state.update_data(account_id=int(message.text))
    
    try:
        await message.delete()
    except:
        pass
    
    data = await state.get_data()
    try:
        await message.bot.delete_message(message.chat.id, data.get('last_bot_message_id'))
    except:
        pass
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔑 Змінити пароль", callback_data="edit_password")],
        [InlineKeyboardButton(text="🔢 Макс. коментарів", callback_data="edit_max_comments")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="menu_accounts")]
    ])
    
    msg = await message.answer(
        f"✏️ <b>Редагування акаунту @{account['username']}</b>\n\n"
        f"Поточні налаштування:\n"
        f"Макс. коментарів: {account['max_comments_per_run']}\n\n"
        f"Що хочете змінити?",
        parse_mode='HTML',
        reply_markup=keyboard
    )
    await state.update_data(last_bot_message_id=msg.message_id)
    await state.set_state(AccountStates.edit_menu)

@router.callback_query(F.data == "edit_password", AccountStates.edit_menu)
async def edit_password_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "🔑 <b>РЕДАГУВАННЯ АКАУНТУ</b>\n\nВведіть новий пароль:",
        parse_mode='HTML',
        reply_markup=cancel_markup("menu_accounts")
    )
    await state.update_data(last_bot_message_id=callback.message.message_id)
    await state.set_state(AccountStates.edit_password)
    await callback.answer()

@router.message(AccountStates.edit_password)
async def process_edit_password(message: Message, state: FSMContext):
    data = await state.get_data()
    account_id = data['account_id']
    
    try:
        await message.delete()
    except:
        pass
    
    try:
        await message.bot.delete_message(message.chat.id, data.get('last_bot_message_id'))
    except:
        pass
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад до головного меню", callback_data="menu_accounts")]
    ])
    
    try:
        db.update_account(account_id, password=message.text)
        await message.answer("✅ <b>Пароль змінено!</b>", parse_mode='HTML', reply_markup=keyboard)
        logger.info(f"Змінено пароль для акаунту ID {account_id}")
    except Exception as e:
        await message.answer(f"❌ <b>Помилка:</b> {e}", parse_mode='HTML', reply_markup=keyboard)
        logger.error(f"Помилка зміни пароля: {e}")
    
    await state.clear()

@router.callback_query(F.data == "edit_max_comments", AccountStates.edit_menu)
async def edit_max_comments_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "🔢 <b>РЕДАГУВАННЯ АКАУНТУ</b>\n\nВведіть нову кількість макс. коментарів:",
        parse_mode='HTML',
        reply_markup=cancel_markup("menu_accounts")
    )
    await state.update_data(last_bot_message_id=callback.message.message_id)
    await state.set_state(AccountStates.edit_max_comments)
    await callback.answer()

@router.message(AccountStates.edit_max_comments)
async def process_edit_max_comments(message: Message, state: FSMContext):
    if not message.text.isdigit():
        try:
            await message.delete()
        except:
            pass
        return
    
    data = await state.get_data()
    account_id = data['account_id']
    
    try:
        await message.delete()
    except:
        pass
    
    try:
        await message.bot.delete_message(message.chat.id, data.get('last_bot_message_id'))
    except:
        pass
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад до головного меню", callback_data="menu_accounts")]
    ])
    
    try:
        db.update_account(account_id, max_comments=int(message.text))
        await message.answer(f"✅ <b>Макс. коментарів змінено на {message.text}!</b>", parse_mode='HTML', reply_markup=keyboard)
        logger.info(f"Змінено макс. коментарів для акаунту ID {account_id}")
    except Exception as e:
        await message.answer(f"❌ <b>Помилка:</b> {e}", parse_mode='HTML', reply_markup=keyboard)
        logger.error(f"Помилка зміни макс. коментарів: {e}")
    
    await state.clear()

# ============= УВІМК/ВИМК АКАУНТ =============

@router.callback_query(F.data == "acc_toggle")
async def toggle_account_start(callback: CallbackQuery, state: FSMContext):
    if not is_authorized(callback.from_user.id):
        await callback.answer("❌ Доступ заборонено!", show_alert=True)
        return
    
    accounts = db.get_all_accounts()
    if not accounts:
        await callback.answer("⚠️ Немає акаунтів", show_alert=True)
        return
    
    text = "🔄 <b>УВІМК/ВИМК АКАУНТ</b>\n\nВведіть ID акаунту:\n\n"
    for acc in accounts:
        status = "🟢 Увімкнено" if acc['enabled'] else "🔴 Вимкнено"
        text += f"{acc['id']}. @{acc['username']} - {status}\n"
    
    await callback.message.edit_text(text, parse_mode='HTML', reply_markup=cancel_markup("menu_accounts"))
    await state.update_data(last_bot_message_id=callback.message.message_id)
    await state.set_state(AccountStates.toggle_select)
    await callback.answer()

@router.message(AccountStates.toggle_select)
async def process_toggle_account(message: Message, state: FSMContext):
    if not message.text.isdigit():
        try:
            await message.delete()
        except:
            pass
        return
    
    account = db.get_account(int(message.text))
    if not account:
        try:
            await message.delete()
        except:
            pass
        data = await state.get_data()
        try:
            await message.bot.delete_message(message.chat.id, data.get('last_bot_message_id'))
        except:
            pass
        
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад до головного меню", callback_data="menu_accounts")]
        ])
        await message.answer("❌ <b>Акаунт не знайдено!</b>", parse_mode='HTML', reply_markup=keyboard)
        await state.clear()
        return
    
    try:
        await message.delete()
    except:
        pass
    
    data = await state.get_data()
    try:
        await message.bot.delete_message(message.chat.id, data.get('last_bot_message_id'))
    except:
        pass
    
    new_status = not account['enabled']
    db.update_account(int(message.text), enabled=new_status)
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад до головного меню", callback_data="menu_accounts")]
    ])
    
    status_text = "увімкнено 🟢" if new_status else "вимкнено 🔴"
    await message.answer(f"✅ <b>Акаунт @{account['username']} {status_text}!</b>", parse_mode='HTML', reply_markup=keyboard)
    logger.info(f"Акаунт @{account['username']} {status_text}")
    await state.clear()

# ============= ВИДАЛЕННЯ АКАУНТУ =============

@router.callback_query(F.data == "acc_delete")
async def delete_account_start(callback: CallbackQuery, state: FSMContext):
    if not is_authorized(callback.from_user.id):
        await callback.answer("❌ Доступ заборонено!", show_alert=True)
        return
    
    accounts = db.get_all_accounts()
    if not accounts:
        await callback.answer("⚠️ Немає акаунтів", show_alert=True)
        return
    
    text = "🗑️ <b>ВИДАЛЕННЯ АКАУНТУ</b>\n\nВведіть ID акаунту:\n\n"
    for acc in accounts:
        text += f"{acc['id']}. @{acc['username']}\n"
    
    await callback.message.edit_text(text, parse_mode='HTML', reply_markup=cancel_markup("menu_accounts"))
    await state.update_data(last_bot_message_id=callback.message.message_id)
    await state.set_state(AccountStates.delete_select)
    await callback.answer()

@router.message(AccountStates.delete_select)
async def process_delete_select(message: Message, state: FSMContext):
    if not message.text.isdigit():
        try:
            await message.delete()
        except:
            pass
        return
    
    account = db.get_account(int(message.text))
    if not account:
        try:
            await message.delete()
        except:
            pass
        data = await state.get_data()
        try:
            await message.bot.delete_message(message.chat.id, data.get('last_bot_message_id'))
        except:
            pass
        
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад до головного меню", callback_data="menu_accounts")]
        ])
        await message.answer("❌ <b>Акаунт не знайдено!</b>", parse_mode='HTML', reply_markup=keyboard)
        await state.clear()
        return
    
    await state.update_data(account_id=int(message.text), username=account['username'])
    
    try:
        await message.delete()
    except:
        pass
    
    data = await state.get_data()
    try:
        await message.bot.delete_message(message.chat.id, data.get('last_bot_message_id'))
    except:
        pass
    
    msg = await message.answer(
        f"⚠️ <b>ВИДАЛЕННЯ АКАУНТУ</b>\n\nВидалити акаунт @{account['username']}?",
        parse_mode='HTML',
        reply_markup=confirm_delete_markup("delete_confirm_yes")
    )
    await state.update_data(last_bot_message_id=msg.message_id)
    await state.set_state(AccountStates.delete_confirm)

@router.callback_query(F.data == "delete_confirm_yes", AccountStates.delete_confirm)
async def process_delete_confirm(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад до головного меню", callback_data="menu_accounts")]
    ])
    
    try:
        db.delete_account(data['account_id'])
        await callback.message.edit_text(
            f"✅ <b>Акаунт @{data['username']} видалено!</b>",
            parse_mode='HTML',
            reply_markup=keyboard
        )
        logger.info(f"Видалено акаунт @{data['username']} (ID: {data['account_id']})")
    except Exception as e:
        await callback.message.edit_text(f"❌ <b>Помилка:</b> {e}", parse_mode='HTML', reply_markup=keyboard)
        logger.error(f"Помилка видалення акаунту: {e}")
    
    await state.clear()
    await callback.answer()
