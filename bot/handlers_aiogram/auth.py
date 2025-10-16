from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from bot.utils import is_authorized, authorize_user, logger
from bot.keyboards_aiogram import main_menu_markup
from bot.config import ADMIN_PIN

router = Router()

class AuthStates(StatesGroup):
    waiting_for_pin = State()

@router.message(Command("start"))
async def cmd_start(message: Message):
    welcome_text = """
🤖 <b>THREADS BOT</b>

Привіт! Це бот для автоматичного коментування постів у Threads за ключовими словами.

<b>Для доступу до адмін панелі:</b>
Введіть команду:
<code>/admin PIN_КОД</code>

PIN-код можна отримати у адміністратора.

───────────────────────────────

<b>Бот розроблений завдяки @ds0903</b>
"""
    await message.answer(welcome_text, parse_mode='HTML')

@router.message(Command("admin"))
async def cmd_admin(message: Message, state: FSMContext):
    # Витягуємо PIN з команди
    args = message.text.split(maxsplit=1)
    
    if len(args) < 2:
        await message.answer(
            "🔐 Введіть PIN-код:\n\n"
            "Формат: <code>/admin PIN_КОД</code>",
            parse_mode='HTML'
        )
        return
    
    pin = args[1].strip()
    
    logger.info(f"Спроба входу користувача {message.from_user.id} з PIN: '{pin}' (очікуваний: '{ADMIN_PIN}')")
    
    if pin == ADMIN_PIN:
        authorize_user(message.from_user.id, message.from_user.username)
        await state.clear()
        await show_admin_panel(message)
        logger.info(f"✅ Успішна авторизація користувача {message.from_user.id}")
    else:
        await message.answer("❌ Невірний PIN-код!")
        logger.warning(f"❌ Невдала спроба входу користувача {message.from_user.id}")

async def show_admin_panel(message: Message):
    text = """
═══════════════════════════════════
  🤖 <b>THREADS BOT - АДМІН ПАНЕЛЬ</b>
═══════════════════════════════════

<b>Виберіть опцію:</b>

1️⃣ 👥 <b>Управління акаунтами</b>
2️⃣ 🔑 <b>Управління ключовими словами</b>
3️⃣ 📊 <b>Статистика та історія</b>
4️⃣ ⚙️ <b>Налаштування</b>
5️⃣ 🚀 <b>ЗАПУСТИТИ БОТА</b>
"""
    await message.answer(text, reply_markup=main_menu_markup(), parse_mode='HTML')

@router.callback_query(F.data == "back_main")
async def back_to_main(callback: CallbackQuery):
    if not is_authorized(callback.from_user.id):
        await callback.answer("❌ Доступ заборонено!", show_alert=True)
        return
    
    text = """
═══════════════════════════════════
  🤖 <b>THREADS BOT - АДМІН ПАНЕЛЬ</b>
═══════════════════════════════════

<b>Виберіть опцію:</b>

1️⃣ 👥 <b>Управління акаунтами</b>
2️⃣ 🔑 <b>Управління ключовими словами</b>
3️⃣ 📊 <b>Статистика та історія</b>
4️⃣ ⚙️ <b>Налаштування</b>
5️⃣ 🚀 <b>ЗАПУСТИТИ БОТА</b>
"""
    
    # Перевіряємо чи є документ у повідомленні
    if callback.message.document or callback.message.photo or callback.message.video:
        # Якщо це документ/фото/відео - видаляємо і відправляємо нове
        chat_id = callback.message.chat.id
        try:
            await callback.message.delete()
        except:
            pass
        await callback.bot.send_message(chat_id, text, reply_markup=main_menu_markup(), parse_mode='HTML')
    else:
        # Якщо це звичайне текстове повідомлення - редагуємо
        try:
            await callback.message.edit_text(text, reply_markup=main_menu_markup(), parse_mode='HTML')
        except:
            # Якщо не вдалося редагувати - відправляємо нове
            chat_id = callback.message.chat.id
            try:
                await callback.message.delete()
            except:
                pass
            await callback.bot.send_message(chat_id, text, reply_markup=main_menu_markup(), parse_mode='HTML')
    
    await callback.answer()

@router.callback_query(F.data == "menu_help")
async def show_help(callback: CallbackQuery):
    if not is_authorized(callback.from_user.id):
        await callback.answer("❌ Доступ заборонено!", show_alert=True)
        return
    
    from bot.keyboards_aiogram import back_button_markup
    
    help_text = """
═══════════════════════════════════
  ❓ <b>HELP</b>
═══════════════════════════════════

<b>Threads Bot</b> - автоматизований бот для коментування постів у Threads

<b>Основні функції:</b>

👥 <b>Акаунти</b> - додавайте акаунти Instagram/Threads
🔑 <b>Ключові слова</b> - встановлюйте слова для пошуку
📝 <b>Шаблони</b> - створюйте варіанти коментарів
👤 <b>Підписка</b> - автоматична підписка на авторів
📊 <b>Статистика</b> - відстежуйте результати
⚙️ <b>Налаштування</b> - налаштовуйте затримки
🚀 <b>Запуск</b> - запускайте бота

<b>Бот розроблений завдяки @ds0903</b>
"""
    await callback.message.edit_text(help_text, reply_markup=back_button_markup(), parse_mode='HTML')
    await callback.answer()
