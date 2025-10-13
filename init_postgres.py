"""
Ініціалізація таблиць PostgreSQL
Запусти цей файл ОДИН раз після створення бази
"""
from database import Database

if __name__ == '__main__':
    print("🔄 Створення таблиць PostgreSQL...")
    try:
        db = Database()
        print("✅ ГОТОВО! Таблиці створено в PostgreSQL")
        print("\nТепер можеш запускати бота:")
        print("  python main.py --once")
        print("  або")
        print("  python admin.py")
    except Exception as e:
        print(f"❌ ПОМИЛКА: {e}")
        print("\nПеревір:")
        print("1. Чи запущений PostgreSQL")
        print("2. Чи правильний пароль в .env файлі")
        print("3. Чи існує база threads_bot та користувач danil")
