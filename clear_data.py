import json
import shutil
from pathlib import Path

def clear_data():
    print("🗑️  Очищення даних")
    print("="*60)
    
    data_dir = Path('data')
    
    print("\n⚠️  УВАГА! Це видалить:")
    print("- Всі логи")
    print("- Історію переглянутих постів")
    print("- Збережені сесії браузера")
    print()
    
    confirm = input("Продовжити? (yes/no): ").strip().lower()
    
    if confirm != 'yes':
        print("❌ Скасовано")
        return
    
    last_seen_file = data_dir / 'last_seen.json'
    if last_seen_file.exists():
        with open(last_seen_file, 'w', encoding='utf-8') as f:
            json.dump({}, f)
        print("✅ Очищено last_seen.json")
    
    logs_file = data_dir / 'logs.json'
    if logs_file.exists():
        with open(logs_file, 'w', encoding='utf-8') as f:
            json.dump([], f)
        print("✅ Очищено logs.json")
    
    sessions_dir = data_dir / 'sessions'
    if sessions_dir.exists():
        shutil.rmtree(sessions_dir)
        sessions_dir.mkdir(exist_ok=True)
        print("✅ Очищено sessions/")
    
    print("\n✅ Дані успішно очищено!")


if __name__ == '__main__':
    clear_data()
