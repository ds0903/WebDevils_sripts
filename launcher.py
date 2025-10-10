import sys
import os
from pathlib import Path

def check_requirements():
    try:
        import selenium
        import schedule
        print("✅ Всі залежності встановлені")
        return True
    except ImportError as e:
        print(f"❌ Відсутні залежності: {e}")
        print("\n📦 Встановіть залежності командою:")
        print("pip install -r requirements.txt")
        return False


def check_config():
    config_dir = Path('config')
    
    if not (config_dir / 'accounts.json').exists():
        print("❌ Відсутній файл config/accounts.json")
        return False
    
    if not (config_dir / 'keywords.json').exists():
        print("❌ Відсутній файл config/keywords.json")
        return False
    
    print("✅ Конфігураційні файли знайдено")
    return True


def main_menu():
    print("\n" + "="*60)
    print("🤖 Threads Auto Commenter (Selenium)")
    print("="*60)
    print("\n1. 🚀 Запустити бота (постійна робота)")
    print("2. ⚡ Запустити один раз")
    print("3. 🔐 Тест входу")
    print("4. 📊 Показати статистику")
    print("5. 📜 Переглянути логи")
    print("6. 🗑️  Очистити дані")
    print("7. ⚙️  Перевірити налаштування")
    print("0. ❌ Вихід")
    
    choice = input("\nВиберіть опцію: ").strip()
    
    if choice == '1':
        print("\n▶️  Запуск бота...\n")
        os.system('python main.py')
    
    elif choice == '2':
        print("\n⚡ Запуск один раз...\n")
        os.system('python run_once.py')
    
    elif choice == '3':
        print("\n🔐 Тестування входу...\n")
        os.system('python test_login.py')
    
    elif choice == '4':
        print("\n📊 Завантаження статистики...\n")
        os.system('python stats.py')
    
    elif choice == '5':
        print("\n📜 Останні логи:\n")
        os.system('python view_logs.py')
    
    elif choice == '6':
        print("\n🗑️  Очищення даних...\n")
        os.system('python clear_data.py')
    
    elif choice == '7':
        print("\n⚙️  Перевірка налаштувань...")
        check_requirements()
        check_config()
    
    elif choice == '0':
        print("\n👋 До побачення!")
        sys.exit(0)
    
    else:
        print("\n❌ Невірний вибір!")


def main():
    while True:
        try:
            main_menu()
            input("\nНатисніть Enter для продовження...")
        except KeyboardInterrupt:
            print("\n\n👋 До побачення!")
            break


if __name__ == '__main__':
    main()
