import os
import sys
from database import Database
from datetime import datetime


class AdminPanel:
    def __init__(self):
        self.db = Database()
    
    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def print_header(self, text):
        print("\n" + "=" * 70)
        print(f"  {text}")
        print("=" * 70)
    
    def print_menu(self, title, options):
        self.print_header(title)
        for key, value in options.items():
            print(f"{key}. {value}")
        print("0. Назад")
    
    def get_input(self, prompt):
        return input(f"\n{prompt}: ").strip()
    
    # === ГОЛОВНЕ МЕНЮ ===
    
    def main_menu(self):
        while True:
            self.clear_screen()
            self.print_menu("🤖 THREADS BOT - АДМІН ПАНЕЛЬ", {
                '1': '👥 Управління акаунтами',
                '2': '🔑 Управління ключовими словами',
                '3': '📊 Статистика та історія',
                '4': '⚙️  Налаштування',
                '5': '🚀 ЗАПУСТИТИ БОТА',
            })
            
            choice = self.get_input("Виберіть опцію")
            
            if choice == '1':
                self.accounts_menu()
            elif choice == '2':
                self.keywords_menu()
            elif choice == '3':
                self.statistics_menu()
            elif choice == '4':
                self.settings_menu()
            elif choice == '5':
                self.run_bot()
            elif choice == '0':
                print("\n👋 До побачення!")
                break
            else:
                print("❌ Невірний вибір!")
                input("Натисніть Enter...")
    
    # === АКАУНТИ ===
    
    def accounts_menu(self):
        while True:
            self.clear_screen()
            self.print_header("👥 УПРАВЛІННЯ АКАУНТАМИ")
            
            accounts = self.db.get_all_accounts()
            
            if accounts:
                print("\n📋 Список акаунтів:\n")
                for acc in accounts:
                    status = "🟢" if acc['enabled'] else "🔴"
                    headless = "👁️" if not acc['headless'] else "🔇"
                    print(f"{acc['id']}. {status} {headless} @{acc['username']} "
                          f"(макс: {acc['max_comments_per_run']} коментарів)")
            else:
                print("\n⚠️  Акаунтів ще немає")
            
            print("\n" + "-" * 70)
            print("1. ➕ Додати акаунт")
            print("2. ✏️  Редагувати акаунт")
            print("3. 🗑️  Видалити акаунт")
            print("4. 🔄 Увімкнути/Вимкнути акаунт")
            print("0. Назад")
            
            choice = self.get_input("Виберіть опцію")
            
            if choice == '1':
                self.add_account()
            elif choice == '2':
                self.edit_account()
            elif choice == '3':
                self.delete_account()
            elif choice == '4':
                self.toggle_account()
            elif choice == '0':
                break
    
    def add_account(self):
        print("\n➕ ДОДАВАННЯ НОВОГО АКАУНТУ\n")
        
        username = self.get_input("Username (Instagram/Threads)")
        if not username:
            print("❌ Username обов'язковий!")
            input("Натисніть Enter...")
            return
        
        password = self.get_input("Password")
        if not password:
            print("❌ Password обов'язковий!")
            input("Натисніть Enter...")
            return
        
        max_comments = self.get_input("Макс. коментарів за запуск (за замовчуванням 5)")
        max_comments = int(max_comments) if max_comments.isdigit() else 5
        
        headless = self.get_input("Headless режим? (y/n, за замовчуванням n)").lower() == 'y'
        
        try:
            account_id = self.db.create_account(username, password, max_comments, True, headless)
            print(f"\n✅ Акаунт створено! ID: {account_id}")
        except Exception as e:
            print(f"\n❌ Помилка: {e}")
        
        input("Натисніть Enter...")
    
    def edit_account(self):
        account_id = self.get_input("ID акаунту для редагування")
        if not account_id.isdigit():
            return
        
        account = self.db.get_account(int(account_id))
        if not account:
            print("❌ Акаунт не знайдено!")
            input("Натисніть Enter...")
            return
        
        print(f"\n✏️  РЕДАГУВАННЯ АКАУНТУ @{account['username']}\n")
        print("Натисніть Enter щоб залишити без змін\n")
        
        username = self.get_input(f"Username [{account['username']}]")
        password = self.get_input(f"Password [***]")
        max_comments = self.get_input(f"Макс. коментарів [{account['max_comments_per_run']}]")
        
        updates = {}
        if username:
            updates['username'] = username
        if password:
            updates['password'] = password
        if max_comments.isdigit():
            updates['max_comments'] = int(max_comments)
        
        if updates:
            self.db.update_account(int(account_id), **updates)
            print("\n✅ Акаунт оновлено!")
        else:
            print("\n⚠️  Змін не внесено")
        
        input("Натисніть Enter...")
    
    def delete_account(self):
        account_id = self.get_input("ID акаунту для видалення")
        if not account_id.isdigit():
            return
        
        account = self.db.get_account(int(account_id))
        if not account:
            print("❌ Акаунт не знайдено!")
            input("Натисніть Enter...")
            return
        
        confirm = self.get_input(f"Видалити акаунт @{account['username']}? (yes/no)")
        if confirm.lower() == 'yes':
            self.db.delete_account(int(account_id))
            print("\n✅ Акаунт видалено!")
        else:
            print("\n❌ Скасовано")
        
        input("Натисніть Enter...")
    
    def toggle_account(self):
        account_id = self.get_input("ID акаунту")
        if not account_id.isdigit():
            return
        
        account = self.db.get_account(int(account_id))
        if not account:
            print("❌ Акаунт не знайдено!")
            input("Натисніть Enter...")
            return
        
        new_status = not account['enabled']
        self.db.update_account(int(account_id), enabled=new_status)
        
        status_text = "увімкнено" if new_status else "вимкнено"
        print(f"\n✅ Акаунт @{account['username']} {status_text}!")
        
        input("Натисніть Enter...")
    
    # === КЛЮЧОВІ СЛОВА ===
    
    def keywords_menu(self):
        while True:
            self.clear_screen()
            self.print_header("🔑 УПРАВЛІННЯ КЛЮЧОВИМИ СЛОВАМИ")
            
            keywords = self.db.get_all_keywords()
            
            if keywords:
                print("\n📋 Список ключових слів:\n")
                for kw in keywords:
                    status = "🟢" if kw['enabled'] else "🔴"
                    templates = self.db.get_templates_for_keyword(kw['id'])
                    print(f"{kw['id']}. {status} \"{kw['keyword']}\" ({len(templates)} шаблонів)")
            else:
                print("\n⚠️  Ключових слів ще немає")
            
            print("\n" + "-" * 70)
            print("1. ➕ Додати ключове слово")
            print("2. 📝 Управління шаблонами")
            print("3. 🔄 Увімкнути/Вимкнути")
            print("4. 🗑️  Видалити ключове слово")
            print("0. Назад")
            
            choice = self.get_input("Виберіть опцію")
            
            if choice == '1':
                self.add_keyword()
            elif choice == '2':
                self.manage_templates()
            elif choice == '3':
                self.toggle_keyword()
            elif choice == '4':
                self.delete_keyword()
            elif choice == '0':
                break
    
    def add_keyword(self):
        print("\n➕ ДОДАВАННЯ КЛЮЧОВОГО СЛОВА\n")
        
        keyword = self.get_input("Ключове слово")
        if not keyword:
            print("❌ Ключове слово обов'язкове!")
            input("Натисніть Enter...")
            return
        
        try:
            keyword_id = self.db.create_keyword(keyword, True)
            print(f"\n✅ Ключове слово створено! ID: {keyword_id}")
            print("\nДодайте шаблони коментарів для цього слова:")
            
            while True:
                template = self.get_input("Шаблон коментаря (Enter для завершення)")
                if not template:
                    break
                
                self.db.create_template(keyword_id, template)
                print("✅ Шаблон додано!")
            
        except Exception as e:
            print(f"\n❌ Помилка: {e}")
        
        input("Натисніть Enter...")
    
    def manage_templates(self):
        keyword_id = self.get_input("ID ключового слова")
        if not keyword_id.isdigit():
            return
        
        keyword = self.db.get_keyword(int(keyword_id))
        if not keyword:
            print("❌ Ключове слово не знайдено!")
            input("Натисніть Enter...")
            return
        
        while True:
            self.clear_screen()
            self.print_header(f"📝 ШАБЛОНИ ДЛЯ \"{keyword['keyword']}\"")
            
            templates = self.db.get_templates_for_keyword(int(keyword_id))
            
            if templates:
                print("\n📋 Список шаблонів:\n")
                for idx, tmpl in enumerate(templates, 1):
                    print(f"{tmpl['id']}. {tmpl['template_text']}")
            else:
                print("\n⚠️  Шаблонів ще немає")
            
            print("\n" + "-" * 70)
            print("1. ➕ Додати шаблон")
            print("2. 🗑️  Видалити шаблон")
            print("0. Назад")
            
            choice = self.get_input("Виберіть опцію")
            
            if choice == '1':
                template = self.get_input("Текст шаблону")
                if template:
                    self.db.create_template(int(keyword_id), template)
                    print("✅ Шаблон додано!")
                    input("Натисніть Enter...")
            elif choice == '2':
                template_id = self.get_input("ID шаблону для видалення")
                if template_id.isdigit():
                    self.db.delete_template(int(template_id))
                    print("✅ Шаблон видалено!")
                    input("Натисніть Enter...")
            elif choice == '0':
                break
    
    def toggle_keyword(self):
        keyword_id = self.get_input("ID ключового слова")
        if not keyword_id.isdigit():
            return
        
        keyword = self.db.get_keyword(int(keyword_id))
        if not keyword:
            print("❌ Ключове слово не знайдено!")
            input("Натисніть Enter...")
            return
        
        new_status = not keyword['enabled']
        self.db.update_keyword(int(keyword_id), enabled=new_status)
        
        status_text = "увімкнено" if new_status else "вимкнено"
        print(f"\n✅ Ключове слово \"{keyword['keyword']}\" {status_text}!")
        
        input("Натисніть Enter...")
    
    def delete_keyword(self):
        keyword_id = self.get_input("ID ключового слова для видалення")
        if not keyword_id.isdigit():
            return
        
        keyword = self.db.get_keyword(int(keyword_id))
        if not keyword:
            print("❌ Ключове слово не знайдено!")
            input("Натисніть Enter...")
            return
        
        confirm = self.get_input(f"Видалити ключове слово \"{keyword['keyword']}\"? (yes/no)")
        if confirm.lower() == 'yes':
            self.db.delete_keyword(int(keyword_id))
            print("\n✅ Ключове слово видалено!")
        else:
            print("\n❌ Скасовано")
        
        input("Натисніть Enter...")
    
    # === СТАТИСТИКА ===
    
    def statistics_menu(self):
        while True:
            self.clear_screen()
            self.print_header("📊 СТАТИСТИКА ТА ІСТОРІЯ")
            
            stats = self.db.get_statistics()
            
            print("\n📈 Загальна статистика:\n")
            print(f"Всього коментарів: {stats['total']}")
            print(f"✅ Успішних: {stats['success']}")
            print(f"⚠️  Невдалих: {stats['failed']}")
            print(f"❌ Помилок: {stats['error']}")
            
            if stats['total'] > 0:
                success_rate = (stats['success'] / stats['total']) * 100
                print(f"\n📊 Success Rate: {success_rate:.1f}%")
            
            print("\n" + "-" * 70)
            print("1. 📜 Переглянути історію (останні 50)")
            print("2. 🔍 Переглянути всю історію (останні 200)")
            print("0. Назад")
            
            choice = self.get_input("Виберіть опцію")
            
            if choice == '1':
                self.view_history(50)
            elif choice == '2':
                self.view_history(200)
            elif choice == '0':
                break
    
    def view_history(self, limit):
        self.clear_screen()
        self.print_header(f"📜 ІСТОРІЯ КОМЕНТАРІВ (останні {limit})")
        
        history = self.db.get_comment_history(limit)
        
        if not history:
            print("\n⚠️  Історії ще немає")
        else:
            for item in history:
                status_icon = {
                    'success': '✅',
                    'failed': '⚠️',
                    'error': '❌'
                }.get(item['status'], '❓')
                
                date = datetime.fromisoformat(item['created_at']).strftime('%Y-%m-%d %H:%M')
                
                print(f"\n{status_icon} {date} | @{item['username']} → \"{item['keyword']}\"")
                if item['comment_text']:
                    print(f"   💬 {item['comment_text'][:60]}...")
                if item['error_message']:
                    print(f"   ❗ {item['error_message']}")
        
        input("\nНатисніть Enter...")
    
    # === НАЛАШТУВАННЯ ===
    
    def settings_menu(self):
        while True:
            self.clear_screen()
            self.print_header("⚙️  НАЛАШТУВАННЯ")
            
            settings = self.db.get_all_settings()
            
            print("\n📋 Поточні налаштування:\n")
            for idx, setting in enumerate(settings, 1):
                print(f"{idx}. {setting['description']}")
                print(f"   Ключ: {setting['key']}")
                print(f"   Значення: {setting['value']}\n")
            
            print("-" * 70)
            print("1. ✏️  Редагувати налаштування")
            print("0. Назад")
            
            choice = self.get_input("Виберіть опцію")
            
            if choice == '1':
                self.edit_settings()
            elif choice == '0':
                break
    
    def edit_settings(self):
        settings = self.db.get_all_settings()
        
        print("\n✏️  РЕДАГУВАННЯ НАЛАШТУВАНЬ\n")
        
        for idx, setting in enumerate(settings, 1):
            print(f"{idx}. {setting['description']} [Поточне: {setting['value']}]")
        
        choice = self.get_input("\nВиберіть номер налаштування для зміни (0 для виходу)")
        
        if not choice.isdigit() or int(choice) == 0:
            return
        
        idx = int(choice) - 1
        if 0 <= idx < len(settings):
            setting = settings[idx]
            new_value = self.get_input(f"Нове значення для '{setting['description']}'")
            
            if new_value:
                self.db.update_setting(setting['key'], new_value)
                print("\n✅ Налаштування оновлено!")
            else:
                print("\n❌ Скасовано")
        else:
            print("\n❌ Невірний вибір!")
        
        input("Натисніть Enter...")
    
    # === ЗАПУСК БОТА ===
    
    def run_bot(self):
        self.clear_screen()
        self.print_header("🚀 ЗАПУСК БОТА")
        
        accounts = [a for a in self.db.get_all_accounts() if a['enabled']]
        keywords = [k for k in self.db.get_all_keywords() if k['enabled']]
        
        if not accounts:
            print("\n❌ Немає активних акаунтів!")
            input("Натисніть Enter...")
            return
        
        if not keywords:
            print("\n❌ Немає активних ключових слів!")
            input("Натисніть Enter...")
            return
        
        print(f"\n✅ Активних акаунтів: {len(accounts)}")
        print(f"✅ Активних ключових слів: {len(keywords)}")
        
        print("\n1. 🔄 Запустити один раз")
        print("2. 🔁 Запустити в циклі (кожні X хвилин)")
        print("0. Назад")
        
        choice = self.get_input("Виберіть режим")
        
        if choice == '1':
            print("\n▶️  Запускаємо бота...\n")
            os.system('python main.py --once')
        elif choice == '2':
            print("\n▶️  Запускаємо бота в циклі...\n")
            os.system('python main.py')
        
        input("\nНатисніть Enter...")


def main():
    try:
        admin = AdminPanel()
        admin.main_menu()
    except KeyboardInterrupt:
        print("\n\n👋 До побачення!")
    except Exception as e:
        print(f"\n❌ Помилка: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
