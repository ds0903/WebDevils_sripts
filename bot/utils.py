import logging
import json
import os
import sys

# Додаємо батьківську директорію
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot.config import AUTH_FILE, BOT_LOG_FILE

# Налаштування логування
def setup_logging():
    """Налаштування системи логування"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(BOT_LOG_FILE, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger('TelegramBot')

logger = setup_logging()

# Словник для зберігання станів
user_states = {}

# Словник авторизованих користувачів
authorized_users = set()

def load_authorized_users():
    """Завантажити список авторизованих користувачів"""
    global authorized_users
    try:
        with open(AUTH_FILE, 'r') as f:
            authorized_users = set(json.load(f))
            logger.info(f"Завантажено {len(authorized_users)} авторизованих користувачів")
    except FileNotFoundError:
        authorized_users = set()
        logger.info("Файл авторизації не знайдено, створено новий список")
    except Exception as e:
        authorized_users = set()
        logger.error(f"Помилка завантаження авторизацій: {e}")

def save_authorized_users():
    """Зберегти список авторизованих користувачів"""
    try:
        with open(AUTH_FILE, 'w') as f:
            json.dump(list(authorized_users), f)
        logger.info(f"Збережено {len(authorized_users)} авторизованих користувачів")
    except Exception as e:
        logger.error(f"Помилка збереження авторизацій: {e}")

def is_authorized(user_id):
    """Перевірити чи користувач авторизований"""
    return user_id in authorized_users

def authorize_user(user_id, username=None):
    """Авторизувати користувача"""
    authorized_users.add(user_id)
    save_authorized_users()
    logger.info(f"Користувач {user_id} (@{username}) авторизований")

def save_authorized_user(user_id, username=None):
    """Аліас для authorize_user"""
    authorize_user(user_id, username)

def log_callback(callback_query):
    """Логувати callback запит"""
    logger.info(
        f"Callback від @{callback_query.from_user.username} "
        f"(ID: {callback_query.from_user.id}): {callback_query.data}"
    )

def log_message(message):
    """Логувати повідомлення"""
    logger.info(
        f"Повідомлення від @{message.from_user.username} "
        f"(ID: {message.from_user.id}): {message.text}"
    )

def log_error(error, context=""):
    """Логувати помилку"""
    logger.error(f"{context}: {error}", exc_info=True)
