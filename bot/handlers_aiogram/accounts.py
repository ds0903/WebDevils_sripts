from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
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
    add_headless = State()
    
    edit_select = State()
    edit_password = State()
    edit_max_comments = State()
    edit_headless = State()
    
    toggle_account = State()
    delete_select = State()
    delete_confirm = State()

@router.callback_query(F.data == "menu_accounts")
async def show_accounts_menu(callback: CallbackQuery):
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
            headless = "🔇" if acc['headless'] else "👁️"
            text += f"{acc['id']}. {status} {headless} @{acc['username']}\n"
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
    
    await callback.message.answer(
        "➕ <b>ДОДАВАННЯ АКАУНТУ</b>\n\nВведіть username (Instagram/Threads):",
        parse_mode='HTML',
        reply_markup=cancel_markup()
    )
    await state.set_state(AccountStates.add_username)
    await callback.answer()

@router.message(AccountStates.add_username)
async def process_add_username(message: Message, state: FSMContext):
    if message.text == "❌ Скасувати":
        await state.clear()
        await message.answer("❌ Скасовано", reply_markup=ReplyKeyboardRemove())
        return
    
    await state.update_data(username=message.text)
    await message.answer("Введіть пароль:", reply_markup=cancel_markup())
    await state.set_state(AccountStates.add_password)

@router.message(AccountStates.add_password)
async def process_add_password(message: Message, state: FSMContext):
    if message.text == "❌ Скасувати":
        await state.clear()
        await message.answer("❌ Скасовано", reply_markup=ReplyKeyboardRemove())
        return
    
    await state.update_data(password=message.text)
    await message.answer("Максимум коментарів за запуск? (За замовчуванням 5)", reply_markup=cancel_markup())
    await state.set_state(AccountStates.add_max_comments)

@router.message(AccountStates.add_max_comments)
async def process_add_max_comments(message: Message, state: FSMContext):
    if message.text == "❌ Скасувати":
        await state.clear()
        await message.answer("❌ Скасовано", reply_markup=ReplyKeyboardRemove())
        return
    
    max_comments = int(message.text) if message.text.isdigit() else 5
    await state.update_data(max_comments=max_comments)
    await message.answer("Headless режим (без вікна браузера)?", reply_markup=yes_no_markup())
    await state.set_state(AccountStates.add_headless)

@router.message(AccountStates.add_headless)
async def process_add_headless(message: Message, state: FSMContext):
    if message.text == "❌ Скасувати":
        await state.clear()
        await message.answer("❌ Скасовано", reply_markup=ReplyKeyboardRemove())
        return
    
    headless = message.text.lower() in ['так', 'yes', 'y']
    data = await state.get_data()
    
    try:
        account_id = db.create_account(
            data['username'],
            data['password'],
            data['max_comments'],
            True,
            headless
        )
        await message.answer(
            f"✅ Акаунт створено!\n\nID: {account_id}\nUsername: @{data['username']}\nМакс. коментарів: {data['max_comments']}",
            reply_markup=ReplyKeyboardRemove()
        )
        logger.info(f"Створено акаунт @{data['username']} (ID: {account_id})")
    except Exception as e:
        await message.answer(f"❌ Помилка: {e}", reply_markup=ReplyKeyboardRemove())
        logger.error(f"Помилка створення акаунту: {e}")
    
    await state.clear()

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
    
    await callback.message.answer(text, parse_mode='HTML', reply_markup=cancel_markup())
    await state.set_state(AccountStates.toggle_account)
    await callback.answer()

@router.message(AccountStates.toggle_account)
async def process_toggle_account(message: Message, state: FSMContext):
    if message.text == "❌ Скасувати":
        await state.clear()
        await message.answer("❌ Скасовано", reply_markup=ReplyKeyboardRemove())
        return
    
    if not message.text.isdigit():
        await message.answer("❌ Введіть числове ID")
        return
    
    account = db.get_account(int(message.text))
    if not account:
        await message.answer("❌ Акаунт не знайдено!", reply_markup=ReplyKeyboardRemove())
        await state.clear()
        return
    
    new_status = not account['enabled']
    db.update_account(int(message.text), enabled=new_status)
    
    status_text = "увімкнено 🟢" if new_status else "вимкнено 🔴"
    await message.answer(
        f"✅ Акаунт @{account['username']} {status_text}!",
        reply_markup=ReplyKeyboardRemove()
    )
    logger.info(f"Акаунт @{account['username']} {status_text}")
    await state.clear()

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
    
    await callback.message.answer(text, parse_mode='HTML', reply_markup=cancel_markup())
    await state.set_state(AccountStates.delete_select)
    await callback.answer()

@router.message(AccountStates.delete_select)
async def process_delete_select(message: Message, state: FSMContext):
    if message.text == "❌ Скасувати":
        await state.clear()
        await message.answer("❌ Скасовано", reply_markup=ReplyKeyboardRemove())
        return
    
    if not message.text.isdigit():
        await message.answer("❌ Введіть числове ID")
        return
    
    account = db.get_account(int(message.text))
    if not account:
        await message.answer("❌ Акаунт не знайдено!", reply_markup=ReplyKeyboardRemove())
        await state.clear()
        return
    
    await state.update_data(account_id=int(message.text), username=account['username'])
    await message.answer(
        f"⚠️ Видалити акаунт @{account['username']}?",
        reply_markup=confirm_delete_markup()
    )
    await state.set_state(AccountStates.delete_confirm)

@router.message(AccountStates.delete_confirm)
async def process_delete_confirm(message: Message, state: FSMContext):
    if message.text == '✅ Так, видалити':
        data = await state.get_data()
        db.delete_account(data['account_id'])
        await message.answer(
            f"✅ Акаунт @{data['username']} видалено!",
            reply_markup=ReplyKeyboardRemove()
        )
        logger.info(f"Видалено акаунт @{data['username']} (ID: {data['account_id']})")
    else:
        await message.answer("❌ Скасовано", reply_markup=ReplyKeyboardRemove())
    
    await state.clear()
