from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

def main_menu_markup():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👥 Управління акаунтами", callback_data="menu_accounts")],
        [InlineKeyboardButton(text="🔑 Управління ключовими словами", callback_data="menu_keywords")],
        [InlineKeyboardButton(text="📊 Статистика та історія", callback_data="menu_stats")],
        [InlineKeyboardButton(text="⚙️ Налаштування", callback_data="menu_settings")],
        [InlineKeyboardButton(text="🚀 ЗАПУСТИТИ БОТА", callback_data="menu_run")],
        [InlineKeyboardButton(text="❓ Help", callback_data="menu_help")]
    ])

def accounts_menu_markup():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Додати акаунт", callback_data="acc_add"),
         InlineKeyboardButton(text="✏️ Редагувати", callback_data="acc_edit")],
        [InlineKeyboardButton(text="🔄 Увімк/Вимк", callback_data="acc_toggle"),
         InlineKeyboardButton(text="🗑️ Видалити", callback_data="acc_delete")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_main")]
    ])

def keywords_menu_markup():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Додати слово", callback_data="kw_add"),
         InlineKeyboardButton(text="📝 Шаблони", callback_data="kw_templates")],
        [InlineKeyboardButton(text="🔄 Увімк/Вимк", callback_data="kw_toggle"),
         InlineKeyboardButton(text="👤 Підписка", callback_data="kw_follow")],
        [InlineKeyboardButton(text="🗑️ Видалити", callback_data="kw_delete")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_main")]
    ])

def stats_menu_markup():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📜 Останні 20", callback_data="stats_20"),
         InlineKeyboardButton(text="📜 Останні 50", callback_data="stats_50")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_main")]
    ])

def run_menu_markup():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Один раз", callback_data="run_once"),
         InlineKeyboardButton(text="🔁 В циклі", callback_data="run_loop")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_main")]
    ])

def back_button_markup():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_main")]
    ])

def cancel_markup(callback_data="back_main"):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Скасувати", callback_data=callback_data)]
    ])

def yes_no_markup(yes_callback, no_callback="back_main"):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Так", callback_data=yes_callback),
         InlineKeyboardButton(text="Ні", callback_data=no_callback)],
        [InlineKeyboardButton(text="❌ Скасувати", callback_data="back_main")]
    ])

def confirm_delete_markup(confirm_callback):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Так, видалити", callback_data=confirm_callback),
         InlineKeyboardButton(text="❌ Скасувати", callback_data="back_main")]
    ])
