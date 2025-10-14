from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from database import Database
from bot.utils import is_authorized, logger
from bot.keyboards_aiogram import keywords_menu_markup, cancel_markup

router = Router()
db = Database()

class KeywordStates(StatesGroup):
    add_keyword = State()
    toggle_keyword = State()
    follow_keyword = State()
    delete_keyword = State()
    add_template = State()

@router.callback_query(F.data == "menu_keywords")
async def show_keywords_menu(callback: CallbackQuery):
    if not is_authorized(callback.from_user.id):
        await callback.answer("❌ Доступ заборонено!", show_alert=True)
        return
    
    keywords = db.get_all_keywords()
    
    text = "═══════════════════════════════════\n"
    text += "  🔑 <b>УПРАВЛІННЯ КЛЮЧОВИМИ СЛОВАМИ</b>\n"
    text += "═══════════════════════════════════\n\n"
    
    if keywords:
        text += "📋 <b>Список ключових слів:</b>\n\n"
        for kw in keywords:
            status = "🟢" if kw['enabled'] else "🔴"
            follow = " 👤" if kw.get('should_follow', False) else ""
            templates = db.get_templates_for_keyword(kw['id'])
            text += f"{kw['id']}. {status}{follow} \"{kw['keyword']}\"\n"
            text += f"   {len(templates)} шаблонів\n\n"
    else:
        text += "⚠️ Ключових слів ще немає\n\n"
    
    text += "<b>Виберіть дію:</b>"
    
    await callback.message.edit_text(text, reply_markup=keywords_menu_markup(), parse_mode='HTML')
    await callback.answer()

@router.callback_query(F.data == "kw_add")
async def add_keyword_start(callback: CallbackQuery, state: FSMContext):
    if not is_authorized(callback.from_user.id):
        await callback.answer("❌ Доступ заборонено!", show_alert=True)
        return
    
    await callback.message.answer(
        "✍️ Введіть ключове слово для пошуку постів:\n\nНаприклад: <i>крипто, NFT, блокчейн</i>",
        parse_mode='HTML',
        reply_markup=cancel_markup()
    )
    await state.set_state(KeywordStates.add_keyword)
    await callback.answer()

@router.message(KeywordStates.add_keyword)
async def process_add_keyword(message: Message, state: FSMContext):
    if message.text == "❌ Скасувати":
        await state.clear()
        await message.answer("❌ Скасовано", reply_markup=ReplyKeyboardRemove())
        return
    
    keyword = message.text.strip()
    if not keyword:
        await message.answer("❌ Ключове слово не може бути порожнім!")
        return
    
    try:
        db.add_keyword(keyword)
        await message.answer(f"✅ Ключове слово \"{keyword}\" додано!", reply_markup=ReplyKeyboardRemove())
        logger.info(f"Додано ключове слово: {keyword}")
    except Exception as e:
        await message.answer(f"❌ Помилка: {e}", reply_markup=ReplyKeyboardRemove())
        logger.error(f"Помилка додавання ключового слова: {e}")
    
    await state.clear()

@router.callback_query(F.data == "kw_toggle")
async def toggle_keyword_start(callback: CallbackQuery, state: FSMContext):
    if not is_authorized(callback.from_user.id):
        await callback.answer("❌ Доступ заборонено!", show_alert=True)
        return
    
    keywords = db.get_all_keywords()
    if not keywords:
        await callback.answer("⚠️ Немає ключових слів!", show_alert=True)
        return
    
    text = "🔢 Введіть ID ключового слова для зміни статусу:\n\n"
    text += "\n".join([f"{kw['id']}. {'🟢' if kw['enabled'] else '🔴'} {kw['keyword']}" for kw in keywords])
    
    await callback.message.answer(text, reply_markup=cancel_markup())
    await state.set_state(KeywordStates.toggle_keyword)
    await callback.answer()

@router.message(KeywordStates.toggle_keyword)
async def process_toggle_keyword(message: Message, state: FSMContext):
    if message.text == "❌ Скасувати":
        await state.clear()
        await message.answer("❌ Скасовано", reply_markup=ReplyKeyboardRemove())
        return
    
    try:
        keyword_id = int(message.text)
        db.toggle_keyword(keyword_id)
        await message.answer(f"✅ Статус ключового слова #{keyword_id} змінено!", reply_markup=ReplyKeyboardRemove())
        logger.info(f"Змінено статус ключового слова ID: {keyword_id}")
    except ValueError:
        await message.answer("❌ Введіть коректний ID!")
    except Exception as e:
        await message.answer(f"❌ Помилка: {e}", reply_markup=ReplyKeyboardRemove())
        logger.error(f"Помилка зміни статусу: {e}")
    
    await state.clear()

@router.callback_query(F.data == "kw_follow")
async def follow_keyword_start(callback: CallbackQuery, state: FSMContext):
    if not is_authorized(callback.from_user.id):
        await callback.answer("❌ Доступ заборонено!", show_alert=True)
        return
    
    keywords = db.get_all_keywords()
    if not keywords:
        await callback.answer("⚠️ Немає ключових слів!", show_alert=True)
        return
    
    text = "👤 Введіть ID ключового слова для зміни підписки:\n\n"
    for kw in keywords:
        follow_status = " 👤" if kw.get('should_follow', False) else ""
        text += f"{kw['id']}. {kw['keyword']}{follow_status}\n"
    
    await callback.message.answer(text, reply_markup=cancel_markup())
    await state.set_state(KeywordStates.follow_keyword)
    await callback.answer()

@router.message(KeywordStates.follow_keyword)
async def process_follow_keyword(message: Message, state: FSMContext):
    if message.text == "❌ Скасувати":
        await state.clear()
        await message.answer("❌ Скасовано", reply_markup=ReplyKeyboardRemove())
        return
    
    try:
        keyword_id = int(message.text)
        db.toggle_keyword_follow(keyword_id)
        await message.answer(f"✅ Підписку для ключового слова #{keyword_id} змінено!", reply_markup=ReplyKeyboardRemove())
        logger.info(f"Змінено підписку для ключового слова ID: {keyword_id}")
    except ValueError:
        await message.answer("❌ Введіть коректний ID!")
    except Exception as e:
        await message.answer(f"❌ Помилка: {e}", reply_markup=ReplyKeyboardRemove())
        logger.error(f"Помилка зміни підписки: {e}")
    
    await state.clear()

@router.callback_query(F.data == "kw_delete")
async def delete_keyword_start(callback: CallbackQuery, state: FSMContext):
    if not is_authorized(callback.from_user.id):
        await callback.answer("❌ Доступ заборонено!", show_alert=True)
        return
    
    keywords = db.get_all_keywords()
    if not keywords:
        await callback.answer("⚠️ Немає ключових слів!", show_alert=True)
        return
    
    text = "🗑️ Введіть ID ключового слова для видалення:\n\n"
    text += "\n".join([f"{kw['id']}. {kw['keyword']}" for kw in keywords])
    
    await callback.message.answer(text, reply_markup=cancel_markup())
    await state.set_state(KeywordStates.delete_keyword)
    await callback.answer()

@router.message(KeywordStates.delete_keyword)
async def process_delete_keyword(message: Message, state: FSMContext):
    if message.text == "❌ Скасувати":
        await state.clear()
        await message.answer("❌ Скасовано", reply_markup=ReplyKeyboardRemove())
        return
    
    try:
        keyword_id = int(message.text)
        db.delete_keyword(keyword_id)
        await message.answer(f"✅ Ключове слово #{keyword_id} видалено!", reply_markup=ReplyKeyboardRemove())
        logger.info(f"Видалено ключове слово ID: {keyword_id}")
    except ValueError:
        await message.answer("❌ Введіть коректний ID!")
    except Exception as e:
        await message.answer(f"❌ Помилка: {e}", reply_markup=ReplyKeyboardRemove())
        logger.error(f"Помилка видалення: {e}")
    
    await state.clear()

@router.callback_query(F.data == "kw_templates")
async def templates_menu(callback: CallbackQuery):
    if not is_authorized(callback.from_user.id):
        await callback.answer("❌ Доступ заборонено!", show_alert=True)
        return
    
    keywords = db.get_all_keywords()
    if not keywords:
        await callback.answer("⚠️ Спочатку додайте ключові слова!", show_alert=True)
        return
    
    text = "═══════════════════════════════════\n"
    text += "  📝 <b>ШАБЛОНИ КОМЕНТАРІВ</b>\n"
    text += "═══════════════════════════════════\n\n"
    text += "Виберіть ключове слово:"
    
    markup = InlineKeyboardMarkup(inline_keyboard=[])
    for kw in keywords:
        templates_count = len(db.get_templates_for_keyword(kw['id']))
        markup.inline_keyboard.append([
            InlineKeyboardButton(
                text=f"{kw['keyword']} ({templates_count} шаблонів)",
                callback_data=f"template_select_{kw['id']}"
            )
        ])
    markup.inline_keyboard.append([InlineKeyboardButton(text="◀️ Назад", callback_data="menu_keywords")])
    
    await callback.message.edit_text(text, reply_markup=markup, parse_mode='HTML')
    await callback.answer()

@router.callback_query(F.data.startswith("template_select_"))
async def show_keyword_templates(callback: CallbackQuery):
    if not is_authorized(callback.from_user.id):
        await callback.answer("❌ Доступ заборонено!", show_alert=True)
        return
    
    keyword_id = int(callback.data.split("_")[2])
    keyword = db.get_keyword_by_id(keyword_id)
    templates = db.get_templates_for_keyword(keyword_id)
    
    text = f"═══════════════════════════════════\n"
    text += f"  📝 <b>ШАБЛОНИ: \"{keyword['keyword']}\"</b>\n"
    text += f"═══════════════════════════════════\n\n"
    
    if templates:
        for i, template in enumerate(templates, 1):
            text += f"{i}. {template['template_text']}\n\n"
    else:
        text += "⚠️ Немає шаблонів\n\n"
    
    markup = InlineKeyboardMarkup(inline_keyboard=[])
    markup.inline_keyboard.append([InlineKeyboardButton(text="➕ Додати шаблон", callback_data=f"template_add_{keyword_id}")])
    
    if templates:
        for template in templates:
            markup.inline_keyboard.append([
                InlineKeyboardButton(
                    text=f"🗑️ Видалити: {template['template_text'][:30]}...",
                    callback_data=f"template_delete_{template['id']}_{keyword_id}"
                )
            ])
    
    markup.inline_keyboard.append([InlineKeyboardButton(text="◀️ Назад", callback_data="kw_templates")])
    
    await callback.message.edit_text(text, reply_markup=markup, parse_mode='HTML')
    await callback.answer()

@router.callback_query(F.data.startswith("template_add_"))
async def add_template_start(callback: CallbackQuery, state: FSMContext):
    if not is_authorized(callback.from_user.id):
        await callback.answer("❌ Доступ заборонено!", show_alert=True)
        return
    
    keyword_id = int(callback.data.split("_")[2])
    await state.update_data(keyword_id=keyword_id)
    await callback.message.answer("✍️ Введіть текст шаблону коментаря:", reply_markup=cancel_markup())
    await state.set_state(KeywordStates.add_template)
    await callback.answer()

@router.message(KeywordStates.add_template)
async def process_add_template(message: Message, state: FSMContext):
    if message.text == "❌ Скасувати":
        await state.clear()
        await message.answer("❌ Скасовано", reply_markup=ReplyKeyboardRemove())
        return
    
    template_text = message.text.strip()
    if not template_text:
        await message.answer("❌ Шаблон не може бути порожнім!")
        return
    
    data = await state.get_data()
    try:
        db.add_template(data['keyword_id'], template_text)
        await message.answer("✅ Шаблон додано!", reply_markup=ReplyKeyboardRemove())
        logger.info(f"Додано шаблон для keyword_id: {data['keyword_id']}")
    except Exception as e:
        await message.answer(f"❌ Помилка: {e}", reply_markup=ReplyKeyboardRemove())
        logger.error(f"Помилка додавання шаблону: {e}")
    
    await state.clear()

@router.callback_query(F.data.startswith("template_delete_"))
async def delete_template(callback: CallbackQuery):
    if not is_authorized(callback.from_user.id):
        await callback.answer("❌ Доступ заборонено!", show_alert=True)
        return
    
    template_id = int(callback.data.split("_")[2])
    keyword_id = int(callback.data.split("_")[3])
    
    db.delete_template(template_id)
    await callback.answer("✅ Шаблон видалено!")
    
    # Оновлюємо список шаблонів
    keyword = db.get_keyword_by_id(keyword_id)
    templates = db.get_templates_for_keyword(keyword_id)
    
    text = f"═══════════════════════════════════\n"
    text += f"  📝 <b>ШАБЛОНИ: \"{keyword['keyword']}\"</b>\n"
    text += f"═══════════════════════════════════\n\n"
    
    if templates:
        for i, template in enumerate(templates, 1):
            text += f"{i}. {template['template_text']}\n\n"
    else:
        text += "⚠️ Немає шаблонів\n\n"
    
    markup = InlineKeyboardMarkup(inline_keyboard=[])
    markup.inline_keyboard.append([InlineKeyboardButton(text="➕ Додати шаблон", callback_data=f"template_add_{keyword_id}")])
    
    if templates:
        for template in templates:
            markup.inline_keyboard.append([
                InlineKeyboardButton(
                    text=f"🗑️ Видалити: {template['template_text'][:30]}...",
                    callback_data=f"template_delete_{template['id']}_{keyword_id}"
                )
            ])
    
    markup.inline_keyboard.append([InlineKeyboardButton(text="◀️ Назад", callback_data="kw_templates")])
    
    await callback.message.edit_text(text, reply_markup=markup, parse_mode='HTML')
