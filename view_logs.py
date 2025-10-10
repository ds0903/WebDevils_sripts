import json
from datetime import datetime
from pathlib import Path

def view_logs(limit=20):
    logs_file = Path('data/logs.json')
    
    if not logs_file.exists():
        print("❌ Файл логів не знайдено")
        return
    
    with open(logs_file, 'r', encoding='utf-8') as f:
        logs = json.load(f)
    
    if not logs:
        print("📭 Логів ще немає")
        return
    
    print("\n" + "="*70)
    print(f"📜 ОСТАННІ {limit} ЗАПИСІВ")
    print("="*70)
    
    recent_logs = logs[-limit:]
    
    for log in reversed(recent_logs):
        timestamp = datetime.fromisoformat(log['timestamp'])
        time_str = timestamp.strftime('%Y-%m-%d %H:%M:%S')
        
        status = log['status']
        if status == 'success':
            status_icon = "✅"
        elif status == 'failed':
            status_icon = "⚠️"
        else:
            status_icon = "❌"
        
        print(f"\n{status_icon} {time_str}")
        print(f"   Акаунт: {log.get('account_id', 'N/A')}")
        print(f"   Ключове слово: {log.get('keyword', 'N/A')}")
        print(f"   Пост ID: {log.get('post_id', 'N/A')}")
        
        if log.get('error'):
            print(f"   Помилка: {log['error']}")


if __name__ == '__main__':
    import sys
    
    limit = 20
    if len(sys.argv) > 1:
        try:
            limit = int(sys.argv[1])
        except:
            pass
    
    view_logs(limit)
