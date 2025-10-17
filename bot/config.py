import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
ADMIN_PIN = os.getenv('TELEGRAM_ADMIN_PIN', '1234')

# Шляхи
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
LOGS_DIR = os.path.join(BASE_DIR, 'logs')
AUTH_FILE = os.path.join(DATA_DIR, 'telegram_auth.json')
BOT_LOG_FILE = os.path.join(LOGS_DIR, 'telegram_bot.log')

# Створюємо папки якщо їх немає
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

# Перевірка токена
if not BOT_TOKEN or BOT_TOKEN == 'YOUR_BOT_TOKEN_HERE':
    print("❌ TELEGRAM_BOT_TOKEN не налаштовано в .env файлі!")
    print("Відкрийте .env і вставте токен вашого бота від @BotFather")
    exit(1)
